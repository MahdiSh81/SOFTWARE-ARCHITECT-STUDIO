"""Attributed capture lineage and strict semantic-review accounting.

These records validate supplied evidence; they do not call models, authenticate
reviewers, prove calibration, or turn lexical matches into semantic correctness.
"""
from __future__ import annotations
import copy
import datetime
import re
from skill_registry import loaded_bundle, inventory_bundle

DIMENSIONS = ('correctness', 'evidence', 'risk_handling', 'constraint_adherence', 'usefulness')
HASH = re.compile(r'^[a-f0-9]{64}$')


def _timestamp(value):
    if not isinstance(value, str) or len(value) > 100:
        return False
    try:
        return datetime.datetime.fromisoformat(value.replace('Z', '+00:00')).tzinfo is not None
    except ValueError:
        return False


def validate_review(review, capture=None):
    if not isinstance(review, dict):
        return ['review must be an object']
    issues = []
    allowed = {'reviewer_id', 'capture_id', 'source_hash', 'reviewed_at', 'rubric_version', 'scores', 'critical_failures', 'evidence_refs', 'calibrated', 'calibration_reference', 'conclusion'}
    if set(review) - allowed:
        issues.append('unknown review fields: ' + ', '.join(sorted(set(review) - allowed)))
    for key in ('reviewer_id', 'capture_id', 'conclusion'):
        if not isinstance(review.get(key), str) or not review[key].strip() or len(review[key]) > 4000:
            issues.append(key + ' must be a bounded nonempty string')
    if type(review.get('rubric_version')) is not int or review['rubric_version'] != 1:
        issues.append('rubric_version must be 1')
    if not isinstance(review.get('source_hash'), str) or not HASH.fullmatch(review['source_hash']):
        issues.append('source_hash must identify the reviewed capture content')
    if not _timestamp(review.get('reviewed_at')):
        issues.append('reviewed_at requires ISO-8601 timezone')
    scores = review.get('scores')
    if not isinstance(scores, dict) or set(scores) != set(DIMENSIONS):
        issues.append('scores must contain exactly the five rubric dimensions')
    elif any(type(score) is not int or not 0 <= score <= 4 for score in scores.values()):
        issues.append('scores must be integers from 0 through 4')
    for key in ('critical_failures', 'evidence_refs'):
        if not isinstance(review.get(key), list) or len(review[key]) > 100 or any(not isinstance(v, str) or not v.strip() or len(v) > 4000 for v in review[key]):
            issues.append(key + ' must be a bounded string array')
    if type(review.get('calibrated')) is not bool:
        issues.append('calibrated must be boolean')
    elif review['calibrated'] and (not isinstance(review.get('calibration_reference'), str) or not review['calibration_reference'].strip()):
        issues.append('calibrated review requires calibration_reference')
    if capture is not None:
        if review.get('capture_id') != capture.get('id'):
            issues.append('capture_id does not match capture')
        expected = capture_identity(capture)
        if review.get('source_hash') != expected:
            issues.append('source_hash does not match reviewed capture content')
    return issues


def capture_identity(capture):
    from codec import digest
    # The reviewed response and its declared provenance are fixed independently of reviews.
    return digest({key: value for key, value in capture.items() if key not in {'reviews', 'rubric', 'critical_failures', 'quality_status', 'review_source_hash'}})


def enrich_capture(capture, root=None, skills=None, references=None):
    if not isinstance(capture, dict):
        raise ValueError('capture must be an object')
    out = copy.deepcopy(capture)
    out['declared_loaded_bundle'] = loaded_bundle(root, skills, references)
    out['available_skill_bundle'] = inventory_bundle(root)
    out['lineage_note'] = 'Loaded files are caller declared; available bundle is repository inventory, not proof all files entered model context.'
    out['review_source_hash'] = capture_identity(out)
    return out


def summarize_captures(captures):
    if not isinstance(captures, list) or len(captures) > 10_000:
        raise ValueError('bounded captures array required')
    seen = set()
    reviewed = calibrated = 0
    unreviewed, critical, disagreements, assessments = [], [], [], []
    for capture in captures:
        if not isinstance(capture, dict) or not isinstance(capture.get('id'), str) or not capture['id'] or len(capture['id']) > 128:
            raise ValueError('capture requires stable nonempty id')
        if capture['id'] in seen:
            raise ValueError('duplicate capture id: ' + capture['id'])
        seen.add(capture['id'])
        reviews = capture.get('reviews', [])
        if not isinstance(reviews, list) or len(reviews) > 100:
            raise ValueError('bounded reviews array required')
        assessors = set()
        for review in reviews:
            issues = validate_review(review, capture)
            if issues:
                raise ValueError('invalid review for ' + capture['id'] + ': ' + '; '.join(issues))
            if review['reviewer_id'] in assessors:
                raise ValueError('duplicate reviewer for capture: ' + review['reviewer_id'])
            assessors.add(review['reviewer_id'])
        if not reviews:
            unreviewed.append(capture['id'])
            assessments.append({'capture': capture['id'], 'status': 'unreviewed'})
            continue
        reviewed += 1
        failures = sorted({v for review in reviews for v in review['critical_failures']})
        if failures:
            critical.append({'capture': capture['id'], 'failures': failures})
        differing = [key for key in DIMENSIONS if len({v['scores'][key] for v in reviews}) > 1]
        if differing:
            disagreements.append({'capture': capture['id'], 'dimensions': differing, 'reviewers': sorted(assessors)})
        complete = len(reviews) >= 2 and all(v['calibrated'] for v in reviews)
        calibrated += int(complete)
        low = any(score < 3 for review in reviews for score in review['scores'].values())
        status = 'failed' if failures or low else 'adjudication_needed' if differing else 'review_complete' if complete else 'review_present'
        assessments.append({'capture': capture['id'], 'status': status, 'reviewers': sorted(assessors), 'attributed_calibration_complete': complete})
    return {'captures': len(captures), 'reviewed': reviewed, 'calibrated_reviewed': calibrated,
            'unreviewed_ids': unreviewed, 'critical_failures': critical, 'disagreements': disagreements,
            'assessments': assessments,
            'semantic_gate_passed': bool(captures) and all(x['status'] == 'review_complete' for x in assessments),
            'assessor_disagreement': 'retain each attributed review; no majority truth inference',
            'scope': 'validated supplied review accounting; reviewer identity/calibration and representativeness are attributed, not authenticated; no live model or user study performed'}


def summarize_observations(records):
    """Summarize explicitly consented caller-supplied task observations, not interviews."""
    import math
    if not isinstance(records, list) or len(records) > 10_000:
        raise ValueError('bounded observations array required')
    seen = set()
    groups = {}
    for record in records:
        if not isinstance(record, dict) or record.get('consented') is not True:
            raise ValueError('each observation requires explicit consented=true')
        if set(record) - {'id', 'participant_alias', 'task', 'consented', 'completed', 'time_seconds', 'corrections'}:
            raise ValueError('unknown observation fields; keep private notes separately')
        for key in ('id', 'participant_alias', 'task'):
            if not isinstance(record.get(key), str) or not record[key].strip() or len(record[key]) > 256:
                raise ValueError(key + ' requires a bounded nonempty string')
        if record['id'] in seen:
            raise ValueError('duplicate observation id')
        seen.add(record['id'])
        completed = record.get('completed')
        if completed is not None and type(completed) is not bool:
            raise ValueError('completed must be boolean or unknown/null')
        seconds, corrections = record.get('time_seconds'), record.get('corrections')
        if seconds is not None and (type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 <= seconds <= 86400):
            raise ValueError('time_seconds must be bounded finite nonnegative number or null')
        if corrections is not None and (type(corrections) is not int or not 0 <= corrections <= 10_000):
            raise ValueError('corrections must be bounded nonnegative integer or null')
        group = groups.setdefault(record['task'], {'observations': 0, 'completed': 0, 'failed': 0, 'completion_unknown': 0, 'measured_time_seconds': [], 'measured_corrections': []})
        group['observations'] += 1
        group['completed' if completed is True else 'failed' if completed is False else 'completion_unknown'] += 1
        if seconds is not None:
            group['measured_time_seconds'].append(seconds)
        if corrections is not None:
            group['measured_corrections'].append(corrections)
    return {'observations': len(records), 'tasks': groups,
            'scope': 'caller-supplied consented task observations; no outreach, interviews, causal inference or representative-population claim',
            'privacy': 'summary excludes participant aliases and free-text notes; keep original observations private under the agreed retention policy'}
