"""Assemble audit documents outside the audited checkout; never mutates source."""
from pathlib import Path
import re,json,csv
ROOT=Path(__file__).resolve().parent
# Canonical IDs consolidate independently discovered duplicates; local IDs remain evidence aliases.
ROWS=[
('PROD-001','E01-F01','Preference changes discard unapplied text','P1','verified defect','I03','Draft survives preference/navigation changes'),
('PROD-002','E01-F02','Record draft crosses collection boundary','P1','verified defect','I03','Collection/type identity mismatch refused without draft loss'),
('PROD-003','E01-F04','New/sample guards ignore meaningful work','P1','verified defect','I03','Every populated field and unsaved draft protected'),
('PROD-004','E01-F05','Beginner record authoring depends on raw JSON','P2','usability opportunity','I08','Representative authoring task succeeds without schema guessing'),
('PROD-005','E01-F06','Continuation packet loses purpose/identity context','P2','scope gap','I05','Resume includes bounded purpose and stable identity'),
('PROD-006','E01-F07','Browser-to-CLI path is not guided','P2','workflow gap','I08','Fresh export reaches documented dry-run/check path'),
('PROD-007','E01-F08','Product demand and user value unmeasured','P2','unmeasured outcome','I11','Consented representative user-task observations retained'),
('OPS-001','E01-F09 E07-F09 E08-F07 E09-F02 E10-F01','Release identities conflict','P1','verified inconsistency','I01','Current manifests/toolkit/display identities agree'),
('ARCH-001','E02-F01','Native and interface contracts disagree while correspondence passes','P1','verified defect','I02','Conflicting response/body/security/parameters block publication'),
('ARCH-002','E02-F02','Accepted project cannot fit revision envelope','P1','verified defect','I05','All advertised payload sizes commit/recover or fail at preflight'),
('ARCH-003','E02-F03','Schema and Python/JS core validators disagree','P1','verified defect','I02','Shared known-field conformance corpus agrees across surfaces'),
('REG-001','E02-F04 E03-F04 E05-F01 E06-F04 E10-F03','Projection identity names intermediate rather than exported representation','P1','verified regression','I02','Each hash recomputes from its explicitly named representation'),
('REPO-001','E02-F05 E04-F03','Nonrequirement record changes do not seed impact','P1','verified omission','I06','Interface/ADR/data-only deltas produce witnesses or scoped unknown'),
('ARCH-004','E02-F06 E01-F03 E03-F02','Readiness lacks shared contract resolution and explicit applicability','P1','scope gap and false blocker','I02','Native-equivalent contracts agree; empty application scope not implementation-ready'),
('QA-001','E02-F07','SQLite failures escape typed CLI error boundary','P2','verified defect','I05','Duplicate-table fixture returns bounded typed JSON, no traceback'),
('GOV-001','E02-F08','Project identity policy differs across browser/revision workflows','P2','integration design risk','I05','Stable identity with explicit legacy/import/fork semantics'),
('CODE-001','E02-F09 E03-F01','Execution adapter is documented but not connected','P1','expanded-scope missing capability','I09','One real source-bound edit/build/check/reconcile workflow demonstrated'),
('ARCH-005','E02-F10','Policy/contract/effect seams are mixed','P2','maintainability opportunity','I07','Pure resolver/result seams without service rewrite'),
('CODE-002','E03-F03','Shareable project export loses native contract context and cannot regenerate','P1','verified defect','I02','Rich default export reloads and recompiles without missing security scheme'),
('INT-001','E03-F05 E06-F05 E08-F01','Receipt schema and runtime validators diverge','P1','verified contract divergence','I04','Schema/runtime agree on null/missing/invalid hashes and statuses'),
('INT-002','E03-F06 E08-F05','Execution effects and source/result binding need explicit adapter policy','P1','integration design risk','I09','Conflict/partial-write/idempotency/authorization fixture suite passes'),
('GOV-002','E03-F07','Implementation evidence does not close the intent verification loop','P2','missing capability','I09','Only source-matched actual checks update verification proposals'),
('SKILL-001','E03-F08 E07-F05','Specialist guidance lacks operational recipes and measured program outcomes','P2','coverage gap','I08','Versioned recipes plus positive/negative activation and end-task tests'),
('REPO-002','E04-F01','Fitness treats file read as sufficient extractor evidence','P1','verified false success','I06','Unsupported/parse-failed relevant files yield unknown'),
('REPO-003','E04-F02','Warm cache erases parse/adapter omissions','P1','verified defect','I06','Cold/warm diagnostics, scope and coverage equivalent'),
('REPO-004','E04-F04','Descriptor edge limits silently truncate','P2','verified omission','I06','Every capped collection reports omission/truncation'),
('REPO-005','E04-F05 E09-F05','Descriptor parse failure can appear as empty successful extraction','P2','verified defect and language limit','I06','Invalid supported descriptor produces explicit parse failure'),
('REPO-006','E04-F06','Python relative import identity is discarded','P2','verified evidence loss','I06','Relative level/module retained without guessing resolution'),
('REPO-007','E04-F07','JS/TS token import attributed to unrelated preceding export','P2','verified false observation','I06','Positive/negative module-token corpus yields precise spans'),
('REPO-008','E04-F08','Reached optional records omitted from affected groups','P2','verified output omission','I06','Verifications/optional groups returned or explicit filter disclosed'),
('REPO-009','E04-F09','Optional cache can abort valid scan; parser deadline is cooperative','P2','verified availability gap and limit','I06','Cache overflow degrades safely; parse budget limitation explicit'),
('REPO-010','E04-F10','Evidence delta lacks envelope/source comparability validation','P2','input validation gap','I06','Unrelated/incompatible/partial scopes rejected or labeled incomparable'),
('REPO-011','E04-F11','Modernization/freshness are instruments, not semantic analysis','P2','honest capability boundary','I10','Language-specific demand-backed seam/drift fixtures before expansion'),
('QA-002','E05-F02 E09-F01','CI verifier absent; release inventory stale/incomplete','P1','verified release defect','I01','All CI targets exist; fresh inventory detects actual tracked mismatches'),
('QA-003','E05-F03','YAML/alternate filename bypasses cross-artifact correspondence','P1','verified false success','I02','Equivalent JSON/YAML/naming variants receive same required checks'),
('SEC-001','E06-F02','Authentication intent disappears from review-ready OpenAPI projection','P1','verified contract defect','I02','Typed required/public intent and native security reconcile consistently'),
('SEC-002','E05-F04','Non-OAuth scheme accepts nonempty scopes','P2','verified semantic validation gap','I02','Unsupported scopes fail despite library schema acceptance'),
('QA-004','E05-F05','Duplicate keys erase invalid input before validation','P2','verified parser integrity gap','I02','Duplicate mapping keys rejected in JSON/YAML'),
('QA-005','E05-F06','Empty output counts as successful renderer result','P2','verified false success','I04','Fresh nonempty valid expected artifact required for render pass'),
('AI-001','E05-F07 E07-F02 E10-F05','Unsafe keyword-stuffed responses pass lexical harness','P2','documented semantic limitation','I11','Actual provenance-bound semantic holdout evaluation before quality claims'),
('SEC-003','E06-F01','Auxiliary receipt can overwrite explicitly selected project/source path','P1','verified accidental data-loss path','I04','Non-clobber destinations preflight before primary side effects'),
('SEC-004','E06-F03','Imported Accepted prose promoted into active AGENTS.md without provenance','P1','verified generation; downstream threat conditional','I04','Default structured constraints; explicit scoped instruction export only'),
('SEC-005','E06-F06','Opt-in editable cache can hide fitness violation','P2','conditional cache trust risk','I06','Release fitness re-extracts untrusted cache; no false clean from forged edge list'),
('OPS-002','E06-F07 E09-F03','CI resolution not bound to transitive inventory/immutable actions','P2','reproducibility risk','I01','Reviewed platform-supported locks and immutable action policy used'),
('SEC-006','E06-F08','Validator diagnostics echo confidential input','P2','verified local disclosure channel','I04','Default diagnostics minimize values; raw debug explicitly private'),
('SEC-007','E06-F09','Browser test server binds all interfaces and serves repository root','P2','configuration exposure risk','I04','Loopback fixture-only server; no repository metadata exposure'),
('INT-003','E08-F02','Malformed untrusted record can crash contract validation','P1','verified input handling defect','I04','Every JSON field shape returns bounded typed issues, no exceptions'),
('GOV-003','E08-F03 E09-F04 E10-F04','Minimized run receipts omit failed gate and operation identity','P2','verified observability limitation','I04','Failure/error/partial outcomes and correlation retained without raw secrets'),
('INT-004','E08-F04','Receipt failure conceals an already committed primary operation','P1','verified partial-effect reporting defect','I04','Post-commit auxiliary failure reports committed state and receipt failure separately'),
('INT-005','E08-F06','Generic full gate checks unknown integration JSON syntax only','P2','documented dispatch scope gap','I04','Explicit schema/kind validation; no schema-coverage inference from syntax pass'),
('OPS-003','E09-F06','Operational guidance does not produce an executable operational handoff','P2','expanded-scope capability gap','I10','Optional workload/SLO/recovery/runbook profile with exact unknowns'),
('SKILL-002','E07-F01','Repository coordinator lacks explicit specialist routing contract','P2','instruction coverage risk, activation unmeasured','I08','Small routing registry and positive/negative task-owner evaluations'),
('GOV-004','E07-F03','Capture hashes root skill only, not loaded specialist/reference bundle','P2','verified provenance limitation','I08','Loaded-source manifest and bundle identity reflect actual references/skills'),
('GOV-005','E07-F04 E10-F06','Review accounting counts malformed/duplicate reviews without validated lineage','P2','verified accounting limitation','I11','Typed rubric/reviewer/source records and distinct calibrated-review status'),
('SKILL-003','E07-F06','Four lifecycle specialty playbooks missing operational coverage','P2','expanded-scope coverage gap','I08','Four conditional 22-field specs with actual capability/fallback checks'),
('AI-002','E07-F07','Context volume known but latency/quality cost unmeasured','P2','measurement opportunity','I11','Selective loading benchmarked without removing safety/context obligations'),
('AI-003','E07-F08','Specialist review plan correctly declares no executed agents','P2','strength and capability boundary','I08','Preserve plan-only honesty and actual worker ledger when available'),
('GOV-006','E10-F02','Repeated supersession creates contradictory lifecycle/provenance','P1','verified lifecycle defect','I05','Valid chains reciprocal/acyclic, stale successor rejected, proposed approval distinct'),
]

def collect():
    raw={}
    for p in sorted((ROOT/'reviewers').glob('expert[0-9][0-9].md')):
        text=p.read_text()
        chunks=re.split(r'(?=^(?:#{1,6} |\*\*)E\d\d-F\d+)',text,flags=re.M)
        for chunk in chunks:
            m=re.match(r'(?:#{1,6} |\*\*)(E\d\d-F\d+)[^\n]*',chunk)
            if m:raw[m.group(1)]={'report':str(p.relative_to(ROOT)),'text':chunk.strip()}
    findings=[]
    for id,aliases,title,priority,kind,initiative,acceptance in ROWS:
        a=aliases.split(); found=[raw[x] for x in a if x in raw]
        findings.append({'id':id,'title':title,'priority':priority,'classification':kind,'confidence':'high for reproduced/source-observed behavior; outcome claims remain scoped','expert_aliases':a,'reports':sorted({x['report'] for x in found}),'initiative':initiative,'recommendation':'Implement the linked initiative and specification; preserve current invariants and independent terminal statuses.','acceptance':acceptance,'evidence_excerpts':found})
    return raw,findings

if __name__=='__main__':
    raw,findings=collect()
    (ROOT/'findings.json').write_text(json.dumps(findings,indent=2)+'\n')
    with (ROOT/'findings.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['id','title','priority','classification','expert_aliases','initiative','acceptance','reports'])
        for x in findings:w.writerow([x[k] if not isinstance(x[k],list) else '; '.join(x[k]) for k in ['id','title','priority','classification','expert_aliases','initiative','acceptance','reports']])
    lines=['# Consolidated finding register','', 'Canonical IDs group duplicate observations. Local expert IDs preserve attribution and detailed evidence, impact, remedy, residual risk and acceptance in the linked reports. Priority is action order, not an exploit severity score. No verified remote P0 exploit was established.','', '| ID | Priority / classification | Finding and evidence aliases | Initiative / acceptance |','|---|---|---|---|']
    for x in findings:
        refs=', '.join(f'[{a}]({raw[a]["report"]})' if a in raw else a for a in x['expert_aliases'])
        lines.append(f'| {x["id"]} | {x["priority"]}; {x["classification"]} | {x["title"]}. {refs} | {x["initiative"]}: {x["acceptance"]} |')
    covered={a for x in findings for a in x['expert_aliases']}
    missing=sorted(set(raw)-covered)
    lines += ['',f'Register: {len(findings)} consolidated findings; {len(covered & set(raw))} expert finding aliases mapped.',f'Unmapped expert aliases: {", ".join(missing) if missing else "none"}.','']
    (ROOT/'finding-register.md').write_text('\n'.join(lines))
    print(json.dumps({'findings':len(findings),'raw_findings':len(raw),'unmapped':missing}))
