"""Bounded regular-file IO. POSIX uses descriptor-relative no-follow operations.

These controls are local filesystem controls, not a sandbox for external tools.
Locking serializes cooperating writers; it is not distributed consensus.
"""
from __future__ import annotations
import contextlib, os, stat, time, uuid
from pathlib import Path
from codec import digest, dumps, strict_json_loads

MAX_BYTES = 5 * 1024 * 1024

def guard(path, root=None):
    path = Path(os.path.abspath(path))
    if root is not None:
        try: path.relative_to(Path(os.path.abspath(root)))
        except ValueError: raise ValueError('path escapes allowed root')
    for part in [*reversed(path.parents), path]:
        try:
            if stat.S_ISLNK(part.lstat().st_mode): raise ValueError(f'symlink disallowed: {part.name}')
        except FileNotFoundError: pass
    return path

@contextlib.contextmanager
def parent_fd(path, create=False):
    path=guard(path)
    if os.name != 'posix' or not hasattr(os, 'O_NOFOLLOW'):
        if create: path.parent.mkdir(parents=True, exist_ok=True)
        guard(path)
        yield None, str(path)
        return
    fd=os.open(path.anchor, os.O_RDONLY|os.O_DIRECTORY)
    try:
        for part in path.parent.parts[1:]:
            if create:
                try: os.mkdir(part, 0o700, dir_fd=fd)
                except FileExistsError: pass
            next_fd=os.open(part, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd);fd=next_fd
        yield fd,path.name
    finally: os.close(fd)

def read_bytes(path, maximum=MAX_BYTES):
    if type(maximum) is not int or maximum < 1: raise ValueError('positive read budget required')
    with parent_fd(path) as (parent,name):
        flags=os.O_RDONLY|getattr(os,'O_NONBLOCK',0)|getattr(os,'O_NOFOLLOW',0)
        fd=os.open(name, flags, dir_fd=parent)
        try:
            info=os.fstat(fd)
            if not stat.S_ISREG(info.st_mode): raise ValueError('regular file required')
            if info.st_size>maximum: raise ValueError('input byte budget exceeded')
            chunks=[];remaining=maximum+1
            while remaining:
                b=os.read(fd,min(65536,remaining))
                if not b: break
                chunks.append(b);remaining-=len(b)
            data=b''.join(chunks)
            if len(data)>maximum: raise ValueError('input byte budget exceeded')
            return data
        finally: os.close(fd)

def read_text(path, maximum=MAX_BYTES):
    return read_bytes(path,maximum).decode('utf-8-sig')

def read_json(path, maximum=MAX_BYTES):
    return strict_json_loads(read_text(path,maximum))

def atomic_write(path, data, exclusive=False, *, maximum=MAX_BYTES):
    if type(maximum) is not int or not 0 < maximum <= 64 * 1024 * 1024:
        raise ValueError('write budget must be a positive integer at most 64 MiB')
    data=data.encode('utf-8') if isinstance(data,str) else data
    if len(data)>maximum: raise ValueError('output byte budget exceeded')
    with parent_fd(path,create=True) as (parent,name):
        try:
            info=os.stat(name,dir_fd=parent,follow_symlinks=False)
            if exclusive: raise FileExistsError(str(path))
            if not stat.S_ISREG(info.st_mode): raise ValueError('non-regular output disallowed')
        except FileNotFoundError: pass
        temp='.'+Path(name).name+'.tmp-'+uuid.uuid4().hex
        if parent is None:temp=str(Path(name).with_name(temp))
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600,dir_fd=parent)
        try:
            with os.fdopen(fd,'wb') as f: f.write(data);f.flush();os.fsync(f.fileno())
            if exclusive:
                # Atomic no-clobber publication for immutable records.
                os.link(temp,name,src_dir_fd=parent,dst_dir_fd=parent,follow_symlinks=False)
                os.unlink(temp,dir_fd=parent)
            else: os.replace(temp,name,src_dir_fd=parent,dst_dir_fd=parent)
            if parent is not None: os.fsync(parent)
        finally:
            try: os.unlink(temp,dir_fd=parent)
            except FileNotFoundError: pass

def remove_owned(path, expected_hash):
    if digest(read_bytes(path)) != expected_hash: raise ValueError('modified output preserved: '+Path(path).name)
    with parent_fd(path) as (parent,name): os.unlink(name,dir_fd=parent)

@contextlib.contextmanager
def project_lock(root):
    path=guard(Path(root)/'.architecture.lock');token=uuid.uuid4().hex
    atomic_write(path,dumps({'token':token,'pid':os.getpid(),'created':time.time()}),exclusive=True)
    try: yield
    finally:
        if read_json(path).get('token')==token:
            with parent_fd(path) as (parent,name): os.unlink(name,dir_fd=parent)

def io_capabilities():
    return {'regular_file_reads':True,'bounded_reads':True,'posix_descriptor_no_follow':os.name=='posix' and hasattr(os,'O_NOFOLLOW'),
            'writer_concurrency':'cooperating local writers under exclusive lock',
            'power_loss_durability':'fsync attempted; filesystem/platform durability not certified',
            'non_posix':'preflight only; hostile path-race protection not claimed'}
