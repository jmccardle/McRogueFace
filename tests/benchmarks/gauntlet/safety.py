"""Memory safety guards for The Gauntlet.

The Gauntlet auto-ramps load geometrically until the frame budget breaks. Some
trials (GRID TITAN especially) scale COST but not necessarily FRAME TIME with
load: a huge SxS grid rendered into a fixed viewport can stay under the frame
budget while its cell/layer/TCOD-map allocation grows as S*S. With no memory
ceiling the ramp then walks straight into OOM -- observed hard-locking the
desktop (kernel OOM-killer / swap-thrash) mid-allocation.

Defense in depth, weakest failure mode last:

1. predict_bytes()  -- a trial that can estimate its footprint refuses a load
   whose predicted allocation exceeds the budget BEFORE allocating it. Graceful:
   the ramp records the last passing load and stops.
2. RSS watchdog     -- after any set_load, if resident memory exceeds the
   ceiling the ramp stops gracefully. Catches trials that cannot predict.
3. RLIMIT_AS        -- a hard address-space cap. If 1 and 2 are both outrun by a
   single oversized allocation, the process dies cleanly (std::bad_alloc ->
   abort) instead of taking the machine down. This is the machine-saver, not a
   graceful path -- it exists so a bug in 1/2 can never again lock the desktop.

Budgets are deliberately conservative. On a 24 GB box the default 1500 MB RSS
ceiling / 2500 MB address-space cap keep the whole run to a small fraction of
RAM; tune via env vars MCRF_GAUNTLET_RSS_MB / MCRF_GAUNTLET_AS_MB if needed.
"""
import os
import resource

_PAGE = resource.getpagesize()

DEFAULT_RSS_CEILING_MB = int(os.environ.get("MCRF_GAUNTLET_RSS_MB", "1500"))
DEFAULT_AS_CAP_MB = int(os.environ.get("MCRF_GAUNTLET_AS_MB", "2500"))


def rss_mb():
    """Resident set size of this process, in MB (Linux /proc/self/statm)."""
    with open("/proc/self/statm") as f:
        resident_pages = int(f.read().split()[1])
    return resident_pages * _PAGE / (1024.0 * 1024.0)


def vmsize_mb():
    """Virtual address-space size of this process, in MB."""
    with open("/proc/self/statm") as f:
        vm_pages = int(f.read().split()[0])
    return vm_pages * _PAGE / (1024.0 * 1024.0)


def install_address_space_cap(cap_mb=DEFAULT_AS_CAP_MB):
    """Hard-limit total address space so a runaway allocation aborts the process
    cleanly instead of exhausting system RAM. Returns the effective cap in MB, or
    None if the platform/hard-limit would not allow setting it.

    The cap is max(cap_mb, current_vmsize + 512) so we never set a limit below
    what is already mapped (which would abort immediately on the next malloc)."""
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    except (ValueError, OSError):
        return None
    floor_mb = vmsize_mb() + 512.0
    target_mb = max(float(cap_mb), floor_mb)
    target_bytes = int(target_mb * 1024 * 1024)
    if hard != resource.RLIM_INFINITY and target_bytes > hard:
        target_bytes = hard
    try:
        resource.setrlimit(resource.RLIMIT_AS, (target_bytes, hard))
    except (ValueError, OSError):
        return None
    return target_bytes / (1024.0 * 1024.0)
