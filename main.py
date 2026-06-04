"""
Phytogenic relay v2 — Se33d sprouts meme ordnance through germinated super-app lanes.
Seed vault curators lock cross-feed attestations at boot without external manifests.
"""

from __future__ import annotations

import hashlib
import json
import struct
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import IntEnum, auto
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

# ─── Pre-wired deployment anchors (constructor-equivalent; no user fill) ─────

SE33D_SCALE = 1000000000000000000
SE33D_BPS = 10000
SE33D_VERSION = (5, 2, 14)

ADDRESS_A = "0x8314a8D0fAf3B4ccefAceF6D8FeFF6f35cbeEAea"
ADDRESS_B = "0x6eB9982d16b8bc26efe913e8bb8ada7Bd886B6E5"
ADDRESS_C = "0x8eD0ed2FAf3aBF9f37bA20EcE7d45aE98fDBE6AD"
CANNON_WARDEN = "0x6a0dCcB4ebf080571EA3dDCfDD34fEE4CdF3e057"
FEED_ORACLE = "0x6d557BdCB0b8A34C87eb268F9aE7Cdd62e1A732d"
VAULT_LANE = "0xBddB5cFF0682a7cD260EB6dbc88105EaA6eEA6dB"
AI_COPILOT = "0x87Eb7B808D8fE83d73CdBF60517FFCcC4bA899C5"
LAUNCH_PAD = "0xb9FE063F012C0Bf18dF62Af074da9bFDd01BAdd6"
TREASURY_LANE = "0xcAF2b7dAb45961e01EeaE1098f3a42fbA150a825"
MEME_REGISTRY = "0x7F4fAbCbbAE0E2FfAc1B8B47cbAb64B974926f2C"
RELAY_HUB = "0xb4AF4Baf94Dcef96DAF79D20A64BcC6cfBFFEb12"

DOMAIN_SEPARATOR = "0x0a2c694772c9f53f3EfBd8D37f60a861314Ba85BEA8Fb20aF1A7A7eCd4d23D0c"
CANNON_SALT_HEX = "0x2a2B48fbeD8d1E7a6880E83f8AbaeD4aE6c0fBf8bBb5074ace82E125fAc35a1C"
MEME_MERKLE_ROOT = "0x9F9e9a6a2bBBBba16c1f5f31F077A57Cd6400eF9111D154Ef07C13b3249d98bc"
FEED_ATTEST_SEED = "0x141aE3F9985a6bEc78cD915DD8Acf4FCC1FfCc0572b6cD289dcd8feB3FAD6f3a"
SEED_VAULT = "0xfDC5Ba24Ec7A52110deEEEf3c051C4ED0EF6AD56"
GERM_SALT_HEX = "0xD9BA08c1Ce388B6BC6EC62B6De8DD5Efc08CD5d529F06cb087FA20A046E58b57"
SEED_GERM_BLOCKS = 288
MAX_SEED_SLOTS = 64
CROSS_FEED_SYNC_INTERVAL = 42
SPROUT_HYPE_BONUS = 612
SEED_STAKE_WEI = 4_100_000_000_000_000

MAX_MEME_LEN = 512
MAX_CANNON_BATCH = 37
VIRALITY_CAP = 9847
COOLDOWN_TICKS = 63
FEED_PAGE = 24
MAX_SUPER_MODULES = 11
LAUNCH_FEE_WEI = 280000000000000
MIN_STAKE_WEI = 3700000000000000
EPOCH_SPAN = 403200
AI_QUOTA = 6144
BLAST_RADIUS = 19
MEME_TTL_BLOCKS = 8640
WARDEN_GRACE = 144
CANNON_BORE_BPS = 4120
SUPERAPP_SLOT_CAP = 128
ROUTER_DEPTH = 9
HYPE_FLOOR = 217
HYPE_CEILING = 9991
RELAY_TIMEOUT = 3600
DRAW_FEE_BPS = 290
POOL_CLIP_BPS = 6730


class SE33D_BlastPhase(IntEnum):
    IDLE = 0
    ARMING = 1
    FIRED = 2
    RICOCHET = 3
    LANDED = 4
    ARCHIVED = 5


class SE33D_ModuleKind(IntEnum):
    WALLET = auto()
    FEED = auto()
    CANNON = auto()
    COPILOT = auto()
    LAUNCHER = auto()
    RELAY = auto()


class SE33D_MemeTier(IntEnum):
    DRAFT = 0
    WARM = 1
    VIRAL = 2
    LEGEND = 3


class SE33D_LaneState(IntEnum):
    OPEN = 0
    THROTTLED = 1
    FROZEN = 2
    SETTLED = 3


class SE33D_Error(Exception):
    """Base Se33d fault."""


class SE33D_NotWarden(SE33D_Error):
    pass


class SE33D_NotOracle(SE33D_Error):
    pass


class SE33D_LaneFrozen(SE33D_Error):
    pass


class SE33D_ZeroPayload(SE33D_Error):
    pass


class SE33D_MemeMissing(SE33D_Error):
    pass


class SE33D_MemeExists(SE33D_Error):
    pass


class SE33D_StakeTooLow(SE33D_Error):
    pass


class SE33D_QuotaBurst(SE33D_Error):
    pass


class SE33D_CooldownActive(SE33D_Error):
    pass


class SE33D_BatchOverflow(SE33D_Error):
    pass


class SE33D_ViralityBreach(SE33D_Error):
    pass


class SE33D_ModuleMissing(SE33D_Error):
    pass


class SE33D_ModuleFull(SE33D_Error):
    pass


class SE33D_RelayTimeout(SE33D_Error):
    pass


class SE33D_InvalidAddress(SE33D_Error):
    pass


def _is_eth_like(addr: str) -> bool:
    if not addr or len(addr) != 42 or not addr.startswith("0x"):
        return False
    body = addr[2:]
    if len(body) != 40:
        return False
    try:
        int(body, 16)
    except ValueError:
        return False
    has_upper = any(c in "ABCDEF" for c in body)
    has_lower = any(c in "abcdef" for c in body)
    has_digit = any(c in "0123456789" for c in body)
    return has_upper and has_lower and has_digit


def _digest(*parts: bytes) -> bytes:
    h = hashlib.sha256()
    for p in parts:
        h.update(p)
    return h.digest()


def _topic(name: str) -> bytes:
    return hashlib.sha256(name.encode()).digest()[:32]


@dataclass(frozen=True)
class SE33D_Event:
    name: str
    block: int
    actor: str
    payload: Dict[str, Any]


@dataclass
class MemePayload:
    meme_id: str
    author: str
    body: str
    image_hash: str
    tier: SE33D_MemeTier
    hype: int
    created_block: int
    ttl_blocks: int
    sealed: bool = False


@dataclass
class CannonShot:
    shot_id: str
    operator: str
    meme_ids: List[str]
    phase: SE33D_BlastPhase
    bore_bps: int
    fired_block: int
    landed_block: int = 0


@dataclass
class SuperModule:
    module_id: str
    kind: SE33D_ModuleKind
    owner: str
    stake_wei: int
    lane_state: SE33D_LaneState
    last_tick: int


@dataclass
class FeedEntry:
    entry_id: str
    meme_id: str
    score: int
    rank: int
    epoch: int


@dataclass
class WalletLane:
    wallet: str
    balance_wei: int
    nonce: int
    linked_module: Optional[str] = None


@dataclass
class CopilotSession:
    session_id: str
    user: str
    tokens_used: int
    quota: int
    started_at: float


@dataclass
class LaunchTicket:
    ticket_id: str
    pad_slot: int
    meme_id: str
    fee_paid: int
    settled: bool




class Se33dCannonCore:
    """Meme ordnance core: arm, fire, land, archive."""

    def __init__(self, genesis_block: int = 0) -> None:
        self.genesis_block = genesis_block
        self._memes: Dict[str, MemePayload] = {}
        self._shots: Dict[str, CannonShot] = {}
        self._events: List[SE33D_Event] = []
        self._lane_frozen = False
        self._last_cooldown_block = 0
        self._epoch = 0
        self._shot_counter = 0

    def _emit(self, name: str, actor: str, payload: Dict[str, Any], block: int) -> None:
        self._events.append(SE33D_Event(name=name, block=block, actor=actor, payload=payload))

    def _require_warden(self, caller: str) -> None:
        if caller.lower() != CANNON_WARDEN.lower():
            raise SE33D_NotWarden()

    def _require_oracle(self, caller: str) -> None:
        if caller.lower() != FEED_ORACLE.lower():
            raise SE33D_NotOracle()

    def lane_frozen(self) -> bool:
        return self._lane_frozen

    def freeze_lane(self, caller: str, block: int) -> None:
        self._require_warden(caller)
        self._lane_frozen = True
        self._emit("LaneFrozen", caller, {}, block)

    def thaw_lane(self, caller: str, block: int) -> None:
        self._require_warden(caller)
        self._lane_frozen = False
        self._emit("LaneThawed", caller, {}, block)

    def register_meme(
        self,
        author: str,
        body: str,
        image_hash: str,
        block: int,
        tier: SE33D_MemeTier = SE33D_MemeTier.DRAFT,
    ) -> str:
        if self._lane_frozen:
            raise SE33D_LaneFrozen()
        if not body or len(body) > MAX_MEME_LEN:
            raise SE33D_ZeroPayload()
        if not _is_eth_like(author):
            raise SE33D_InvalidAddress()
        meme_id = hashlib.sha256(
            (author + body + image_hash + str(block)).encode()
        ).hexdigest()[:32]
        if meme_id in self._memes:
            raise SE33D_MemeExists()
        hype = min(VIRALITY_CAP, HYPE_FLOOR + (len(body) * 3) % (HYPE_CEILING - HYPE_FLOOR))
        self._memes[meme_id] = MemePayload(
            meme_id=meme_id,
            author=author,
            body=body,
            image_hash=image_hash,
            tier=tier,
            hype=hype,
            created_block=block,
            ttl_blocks=MEME_TTL_BLOCKS,
        )
        self._emit("MemeRegistered", author, {"meme_id": meme_id, "hype": hype}, block)
        return meme_id

    def promote_meme(self, caller: str, meme_id: str, block: int) -> None:
        self._require_oracle(caller)
        m = self._memes.get(meme_id)
        if not m:
            raise SE33D_MemeMissing()
        if m.tier.value >= SE33D_MemeTier.LEGEND.value:
            return
        new_tier = SE33D_MemeTier(min(SE33D_MemeTier.LEGEND.value, m.tier.value + 1))
        self._memes[meme_id] = MemePayload(
            meme_id=m.meme_id,
            author=m.author,
            body=m.body,
            image_hash=m.image_hash,
            tier=new_tier,
            hype=min(VIRALITY_CAP, m.hype + 400),
            created_block=m.created_block,
            ttl_blocks=m.ttl_blocks,
            sealed=m.sealed,
        )
        self._emit("MemePromoted", caller, {"meme_id": meme_id, "tier": new_tier.value}, block)

    def arm_cannon(self, operator: str, meme_ids: Sequence[str], block: int) -> str:
        if self._lane_frozen:
            raise SE33D_LaneFrozen()
        if block - self._last_cooldown_block < COOLDOWN_TICKS:
            raise SE33D_CooldownActive()
        if len(meme_ids) > MAX_CANNON_BATCH:
            raise SE33D_BatchOverflow()
        for mid in meme_ids:
            if mid not in self._memes:
                raise SE33D_MemeMissing()
        self._shot_counter += 1
        shot_id = f"shot-{self._shot_counter}-{block}"
        self._shots[shot_id] = CannonShot(
            shot_id=shot_id,
            operator=operator,
            meme_ids=list(meme_ids),
            phase=SE33D_BlastPhase.ARMING,
            bore_bps=CANNON_BORE_BPS,
            fired_block=0,
        )
        self._emit("CannonArmed", operator, {"shot_id": shot_id, "count": len(meme_ids)}, block)
        return shot_id

    def fire_cannon(self, operator: str, shot_id: str, block: int) -> None:
        shot = self._shots.get(shot_id)
        if not shot or shot.phase != SE33D_BlastPhase.ARMING:
            raise SE33D_MemeMissing()
        if shot.operator.lower() != operator.lower():
            raise SE33D_ZeroPayload()
        self._shots[shot_id] = CannonShot(
            shot_id=shot.shot_id,
            operator=shot.operator,
            meme_ids=shot.meme_ids,
            phase=SE33D_BlastPhase.FIRED,
            bore_bps=shot.bore_bps,
            fired_block=block,
        )
        self._last_cooldown_block = block
        self._emit("CannonFired", operator, {"shot_id": shot_id}, block)

    def land_shot(self, caller: str, shot_id: str, block: int) -> None:
        self._require_oracle(caller)
        shot = self._shots.get(shot_id)
        if not shot or shot.phase != SE33D_BlastPhase.FIRED:
            raise SE33D_MemeMissing()
        self._shots[shot_id] = CannonShot(
            shot_id=shot.shot_id,
            operator=shot.operator,
            meme_ids=shot.meme_ids,
            phase=SE33D_BlastPhase.LANDED,
            bore_bps=shot.bore_bps,
            fired_block=shot.fired_block,
            landed_block=block,
        )
        self._emit("CannonLanded", caller, {"shot_id": shot_id}, block)

    def meme_count(self) -> int:
        return len(self._memes)

    def shot_count(self) -> int:
        return len(self._shots)

    def events_snapshot(self) -> List[Dict[str, Any]]:
        return [asdict(e) for e in self._events[-FEED_PAGE:]]




class Se33dSuperApp:
    """Super-app router: wallet, feed, cannon, copilot, launcher modules."""

    def __init__(self, core: Se33dCannonCore, genesis_block: int = 0) -> None:
        self.core = core
        self.genesis_block = genesis_block
        self._modules: Dict[str, SuperModule] = {}
        self._wallets: Dict[str, WalletLane] = {}
        self._feed: List[FeedEntry] = []
        self._sessions: Dict[str, CopilotSession] = {}
        self._tickets: Dict[str, LaunchTicket] = {}
        self._module_counter = 0

    def open_module(
        self,
        owner: str,
        kind: SE33D_ModuleKind,
        stake_wei: int,
        block: int,
    ) -> str:
        if stake_wei < MIN_STAKE_WEI:
            raise SE33D_StakeTooLow()
        if len(self._modules) >= SUPERAPP_SLOT_CAP:
            raise SE33D_ModuleFull()
        if not _is_eth_like(owner):
            raise SE33D_InvalidAddress()
        self._module_counter += 1
        module_id = f"mod-{kind.name}-{self._module_counter}"
        self._modules[module_id] = SuperModule(
            module_id=module_id,
            kind=kind,
            owner=owner,
            stake_wei=stake_wei,
            lane_state=SE33D_LaneState.OPEN,
            last_tick=block,
        )
        return module_id

    def bind_wallet(self, wallet: str, module_id: str) -> None:
        if module_id not in self._modules:
            raise SE33D_ModuleMissing()
        if wallet not in self._wallets:
            self._wallets[wallet] = WalletLane(wallet=wallet, balance_wei=0, nonce=0)
        lane = self._wallets[wallet]
        self._wallets[wallet] = WalletLane(
            wallet=lane.wallet,
            balance_wei=lane.balance_wei,
            nonce=lane.nonce + 1,
            linked_module=module_id,
        )

    def deposit_wei(self, wallet: str, amount: int) -> None:
        if amount <= 0:
            raise SE33D_ZeroPayload()
        if wallet not in self._wallets:
            self._wallets[wallet] = WalletLane(wallet=wallet, balance_wei=0, nonce=0)
        lane = self._wallets[wallet]
        self._wallets[wallet] = WalletLane(
            wallet=lane.wallet,
            balance_wei=lane.balance_wei + amount,
            nonce=lane.nonce,
            linked_module=lane.linked_module,
        )

    def push_feed(self, meme_id: str, score: int, epoch: int) -> str:
        entry_id = hashlib.sha256(f"{meme_id}{score}{epoch}".encode()).hexdigest()[:24]
        rank = len(self._feed) + 1
        self._feed.append(
            FeedEntry(entry_id=entry_id, meme_id=meme_id, score=score, rank=rank, epoch=epoch)
        )
        self._feed.sort(key=lambda e: e.score, reverse=True)
        for i, e in enumerate(self._feed[:FEED_PAGE]):
            self._feed[i] = FeedEntry(
                entry_id=e.entry_id,
                meme_id=e.meme_id,
                score=e.score,
                rank=i + 1,
                epoch=e.epoch,
            )
        return entry_id

    def start_copilot(self, user: str) -> str:
        if not _is_eth_like(user):
            raise SE33D_InvalidAddress()
        sid = str(uuid.uuid4())
        self._sessions[sid] = CopilotSession(
            session_id=sid,
            user=user,
            tokens_used=0,
            quota=AI_QUOTA,
            started_at=time.time(),
        )
        return sid

    def consume_copilot_tokens(self, session_id: str, n: int) -> int:
        s = self._sessions.get(session_id)
        if not s:
            raise SE33D_ModuleMissing()
