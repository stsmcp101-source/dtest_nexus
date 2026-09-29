import json
import os
import re
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.permissions.decorators import require_permission

from .forms import (
    AnnouncementForm,
    FortuneSlipUploadForm,
    PlayLimitForm,
    game_play_limit_form,
    PosterImageForm,
    SquaresSettingsForm,
    SquaresWordForm,
    TypingSettingsForm,
    WordleSettingsForm,
)
from .models import (
    Announcement,
    FortuneSlip,
    GamePlay,
    GameScore,
    HappyWorkplaceSettings,
    PosterImage,
    SquaresSettings,
    SquaresWord,
    TypingSettings,
    WordleScore,
    WordleSettings,
)
from .squares import generate_puzzle
from .wordle_words import WORDS as WORDLE_WORDS

_LINE_ICON = '<svg class="hwp-game-icn" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3">{}</svg>'

GAMES = [
    {
        "code": "wordle", "url_name": "happy_workplace:wordle", "tag": "WORD GAME",
        "name": "Wordle", "description": "Daily Challenge ทายคำศัพท์ 5 ตัวอักษร แข่งกับเวลา",
        "icon": (
            '<svg class="hwp-game-icn" viewBox="0 0 40 40">'
            '<rect x="1" y="1" width="38" height="38" rx="10" fill="#6aaa64" stroke="#1c2b18" stroke-width="2"/>'
            '<path d="M9 13l3.4 14h3l3.1-11 3.1 11h3L28 13h-3.1l-1.9 10-2.8-10h-2.4l-2.8 10-1.9-10z" fill="#fff"/>'
            '</svg>'
        ),
    },
    {
        "code": "fortune_stick", "url_name": "happy_workplace:fortune_stick", "tag": "โชคลาภ",
        "name": "เสี่ยงเซียมซี", "description": "เขย่ากระบอกเซียมซี ดูดวงชะตาแบบไทยคลาสสิก",
        "icon": (
            '<svg class="hwp-game-icn" viewBox="0 0 40 40">'
            '<rect x="1" y="1" width="38" height="38" rx="10" fill="#b3273f" stroke="#5c0f1c" stroke-width="2"/>'
            '<line x1="15" y1="21" x2="11" y2="7" stroke="#3d2513" stroke-width="2" stroke-linecap="round"/>'
            '<line x1="19" y1="20" x2="18" y2="4" stroke="#3d2513" stroke-width="2" stroke-linecap="round"/>'
            '<line x1="23" y1="20" x2="24" y2="4" stroke="#3d2513" stroke-width="2" stroke-linecap="round"/>'
            '<line x1="27" y1="21" x2="31" y2="7" stroke="#3d2513" stroke-width="2" stroke-linecap="round"/>'
            '<rect x="9" y="19" width="22" height="17" rx="3" fill="#f2c94c" stroke="#8a4b12" stroke-width="1"/>'
            '<rect x="9" y="19" width="22" height="5" fill="#b3273f"/>'
            '</svg>'
        ),
    },
    {
        "code": "phone_analysis", "url_name": "happy_workplace:phone_analysis", "tag": "เลขศาสตร์",
        "name": "วิเคราะห์เบอร์", "description": "ใส่เบอร์โทรศัพท์ ดูเลขคู่ดี-เสีย และคะแนน 6 ด้านเพื่อความบันเทิง",
        "icon": (
            '<svg class="hwp-game-icn" viewBox="0 0 40 40">'
            '<rect x="1" y="1" width="38" height="38" rx="10" fill="#1f9d8a" stroke="#0b4a41" stroke-width="2"/>'
            '<rect x="12.5" y="7" width="15" height="26" rx="3" fill="#fff"/>'
            '<rect x="14.5" y="10" width="11" height="15" rx="1" fill="#1f9d8a"/>'
            '<text x="20" y="21" text-anchor="middle" font-family="Poppins,Arial,sans-serif" font-size="8" font-weight="700" fill="#fff">789</text>'
            '<circle cx="20" cy="29" r="1.5" fill="#1f9d8a"/>'
            '</svg>'
        ),
    },
    {
        "code": "dream", "url_name": "happy_workplace:dream", "tag": "ความฝัน",
        "name": "ทำนายฝัน", "description": "เล่าความฝันเมื่อคืน รับคำทำนายและเลขนำโชคสนุกๆ",
        "icon": (
            '<svg class="hwp-game-icn" viewBox="0 0 40 40">'
            '<rect x="1" y="1" width="38" height="38" rx="10" fill="#5b4bc4" stroke="#241a66" stroke-width="2"/>'
            '<path d="M26 25.5A9.5 9.5 0 0114.5 12a9.5 9.5 0 1011.5 13.5z" fill="#ffd95a"/>'
            '<path d="M27 8l1.1 2.9L31 12l-2.9 1.1L27 16l-1.1-2.9L23 12l2.9-1.1z" fill="#fff"/>'
            '<circle cx="31" cy="24" r="1.2" fill="#fff"/><circle cx="12" cy="30" r="1" fill="#fff"/>'
            '</svg>'
        ),
    },
]

_GAME_SQUARES = {
    "code": "squares", "url_name": "happy_workplace:squares", "tag": "WORD PUZZLE",
    "name": "Squares", "description": "ลากต่อตัวอักษรให้เป็นศัพท์แอร์และวิศวกรรม ถูกแล้วเห็นความหมายทันที",
    "icon": (
        '<svg class="hwp-game-icn" viewBox="0 0 40 40">'
        '<rect x="1" y="1" width="38" height="38" rx="10" fill="#2f80ed" stroke="#123f80" stroke-width="2"/>'
        '<g fill="#fff"><rect x="7" y="7" width="12.5" height="12.5" rx="2.5"/><rect x="20.5" y="7" width="12.5" height="12.5" rx="2.5"/>'
        '<rect x="7" y="20.5" width="12.5" height="12.5" rx="2.5"/><rect x="20.5" y="20.5" width="12.5" height="12.5" rx="2.5" fill="#ffd95a"/></g>'
        '<g font-family="Poppins,Arial,sans-serif" font-size="9" font-weight="700" fill="#2f80ed" text-anchor="middle">'
        '<text x="13.2" y="16.2">S</text><text x="26.7" y="16.2">Q</text><text x="13.2" y="29.7">U</text></g>'
        '<text x="26.7" y="29.7" font-family="Poppins,Arial,sans-serif" font-size="9" font-weight="700" fill="#7a5b0a" text-anchor="middle">A</text>'
        '</svg>'
    ),
}
_GAME_TYPING = {
    "code": "typing_test", "url_name": "happy_workplace:typing_test", "tag": "SPEED",
    "name": "พิมพ์เร็ว", "description": "พิมพ์ไทย/อังกฤษให้เร็วที่สุดแข่งกับเวลา วัดคำต่อนาทีและความแม่นยำ",
    "icon": (
        '<svg class="hwp-game-icn" viewBox="0 0 40 40">'
        '<rect x="1" y="1" width="38" height="38" rx="10" fill="#ef7d22" stroke="#6b3006" stroke-width="2"/>'
        '<rect x="6" y="12" width="28" height="17" rx="3" fill="#fff"/>'
        '<g fill="#ef7d22"><rect x="9" y="15" width="3.6" height="3.6" rx=".8"/><rect x="14" y="15" width="3.6" height="3.6" rx=".8"/>'
        '<rect x="19" y="15" width="3.6" height="3.6" rx=".8"/><rect x="24" y="15" width="3.6" height="3.6" rx=".8"/>'
        '<rect x="29" y="15" width="2.6" height="3.6" rx=".8"/><rect x="11" y="23" width="18" height="3.4" rx=".8"/></g>'
        '</svg>'
    ),
}
# Display order: Wordle, Squares, typing, fortune stick, phone analysis, dream
GAMES = [GAMES[0], _GAME_SQUARES, _GAME_TYPING] + GAMES[1:]


# ---------------------------------------------------------------------------
# Public pages — no login required, matches the rest of the site's pattern
# of "viewing is public, only mutating requires permission" (see Document
# Data's public download / gated upload for the precedent).
# ---------------------------------------------------------------------------
def index(request):
    return render(request, "happy_workplace/index.html", {
        "announcements": Announcement.objects.all(),
        "posters": PosterImage.objects.all(),
        "games": GAMES,
    })


# ---------------------------------------------------------------------------
# Daily play limit. Players are anonymous, so rounds are counted per browser
# (random id in a long-lived cookie) per game per day. Clearing cookies resets
# a player's count — this is a friendly limit, not a hard security control.
# ---------------------------------------------------------------------------
PLAY_LIMITED_GAMES = ("wordle", "squares", "typing", "fortune", "phone_analysis", "dream")
PLAY_COOKIE = "hwp_cid"
_CID_RE = re.compile(r"^[0-9a-f]{32}$")


def _client_id(request):
    cid = request.COOKIES.get(PLAY_COOKIE, "")
    return cid if _CID_RE.match(cid) else ""


def _play_state(request, game):
    limit = HappyWorkplaceSettings.get_solo().limit_for(game)
    cid = _client_id(request)
    used = 0
    if cid:
        rec = GamePlay.objects.filter(game=game, client_id=cid, day=timezone.localdate()).first()
        used = rec.count if rec else 0
    return {"limit": limit, "used": used, "remaining": None if limit == 0 else max(0, limit - used)}


@require_POST
def play_start(request, game):
    """Called when a round starts. Public; counts the round or refuses it."""
    if game not in PLAY_LIMITED_GAMES:
        return JsonResponse({"ok": False, "error": "unknown game"}, status=404)
    cid = _client_id(request) or uuid.uuid4().hex
    limit = HappyWorkplaceSettings.get_solo().limit_for(game)
    with transaction.atomic():
        rec, _ = GamePlay.objects.select_for_update().get_or_create(
            game=game, client_id=cid, day=timezone.localdate()
        )
        allowed = limit == 0 or rec.count < limit
        if allowed:
            rec.count += 1
            rec.save(update_fields=["count"])
    body = {
        "ok": allowed, "limit": limit,
        "remaining": None if limit == 0 else max(0, limit - rec.count),
    }
    response = JsonResponse(body, status=200 if allowed else 403)
    response.set_cookie(PLAY_COOKIE, cid, max_age=365 * 86400, samesite="Lax", httponly=True)
    return response


PLAY_GAME_PAGES = {
    "wordle": "happy_workplace:wordle", "squares": "happy_workplace:squares", "typing": "happy_workplace:typing_test",
    "fortune": "happy_workplace:fortune_stick", "phone_analysis": "happy_workplace:phone_analysis", "dream": "happy_workplace:dream",
}


@login_required
@require_permission("happy_workplace.edit")
@require_POST
def play_settings_update(request, game=None):
    """Save the daily play limit. With `game`, only that game's value (from its
    settings box) and back to that game's page; without, all three (manage page)."""
    if game is not None and game not in PLAY_LIMITED_GAMES:
        return redirect("happy_workplace:index")
    form_class = game_play_limit_form(game) if game else PlayLimitForm
    form = form_class(request.POST, instance=HappyWorkplaceSettings.get_solo())
    if form.is_valid():
        form.save()
        if game:
            limit = form.cleaned_data[f"{game}_play_limit"]
            messages.success(request, "ตั้งค่าเล่นได้ไม่จำกัดจำนวนครั้งเรียบร้อยแล้ว" if limit == 0 else f"ตั้งค่าเล่นได้วันละ {limit} ครั้งเรียบร้อยแล้ว")
        else:
            messages.success(request, "บันทึกการจำกัดจำนวนครั้งที่เล่นต่อวันเรียบร้อยแล้ว")
    else:
        messages.error(request, "ค่าที่กรอกไม่ถูกต้อง (0-100)")
    return redirect(PLAY_GAME_PAGES[game] if game else "happy_workplace:manage")


@login_required
@require_permission("happy_workplace.edit")
@require_POST
def play_counts_reset(request):
    deleted, _ = GamePlay.objects.filter(day=timezone.localdate()).delete()
    messages.success(request, "รีเซ็ตการนับจำนวนครั้งที่เล่นของวันนี้เรียบร้อยแล้ว")
    return redirect("happy_workplace:manage")


WORDLE_LEADERBOARD_SIZE = 20
WORDLE_MAX_WORDS_PER_SESSION = 500


def _name_key(name):
    return name.strip().casefold()


def _best_per_name(rows, limit):
    """rows must already be ordered best-first; keeps each name's top row."""
    seen, out = set(), []
    for row in rows:
        key = _name_key(row.name)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
        if len(out) == limit:
            break
    return out


def _wordle_leaderboard():
    return [
        {"name": s.name, "score": s.score, "wordsCorrect": s.words_correct}
        for s in _best_per_name(WordleScore.objects.all(), WORDLE_LEADERBOARD_SIZE)
    ]


def wordle(request):
    settings_obj = WordleSettings.get_solo()
    return render(request, "happy_workplace/wordle.html", {
        "wordle_settings": settings_obj,
        "wordle_settings_json": {
            "sessionSeconds": settings_obj.session_minutes * 60,
            "maxGuesses": settings_obj.max_guesses,
            "penaltyPerWrong": settings_obj.penalty_per_wrong,
        },
        "wordle_words": WORDLE_WORDS,
        "settings_form": WordleSettingsForm(instance=settings_obj),
        "leaderboard": _wordle_leaderboard(),
        "play": _play_state(request, "wordle"),
        "play_form": game_play_limit_form("wordle")(instance=HappyWorkplaceSettings.get_solo()),
    })


@require_POST
def wordle_submit_score(request):
    """Public (players don't log in). Values are sanity-checked, but since
    scoring runs in the browser this can't fully prevent a determined
    player from posting a made-up score."""
    try:
        payload = json.loads(request.body)
        name = str(payload.get("name", "")).strip()[:25] or "ไม่ระบุชื่อ"
        score = int(payload["score"])
        words_correct = int(payload["wordsCorrect"])
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"error": "invalid payload"}, status=400)
    if not (0 <= words_correct <= WORDLE_MAX_WORDS_PER_SESSION) or not (0 <= score <= words_correct * 10):
        return JsonResponse({"error": "invalid score"}, status=400)
    same_name = [s for s in WordleScore.objects.all() if _name_key(s.name) == _name_key(name)]
    if not same_name:
        WordleScore.objects.create(name=name, score=score, words_correct=words_correct)
    else:
        best = same_name[0]  # queryset is ordered best-first
        if (score, words_correct) > (best.score, best.words_correct):
            best.name, best.score, best.words_correct = name, score, words_correct
            best.created_at = timezone.now()
            best.save()
        for extra in same_name[1:]:
            extra.delete()
    return JsonResponse({"leaderboard": _wordle_leaderboard()})


@login_required
@require_permission("happy_workplace.edit")
@require_POST
def wordle_settings_update(request):
    form = WordleSettingsForm(request.POST, instance=WordleSettings.get_solo())
    if form.is_valid():
        form.save()
        messages.success(request, "บันทึกการตั้งค่าเกม Wordle เรียบร้อยแล้ว")
    else:
        messages.error(request, "ค่าที่กรอกไม่ถูกต้อง (เวลา 1-60 นาที, จำนวนครั้งที่ทาย 1-20, คะแนนติดลบ 0-10)")
    return redirect("happy_workplace:wordle")


@login_required
@require_permission("happy_workplace.edit")
def wordle_reset_scores(request):
    if request.method == "POST":
        WordleScore.objects.all().delete()
        messages.success(request, "รีเซ็ตตารางคะแนน Wordle เรียบร้อยแล้ว")
        return redirect("happy_workplace:wordle")
    return render(request, "happy_workplace/wordle_confirm_reset.html", {
        "score_count": WordleScore.objects.count(),
    })


FORTUNE_SLIP_MIN = 1
FORTUNE_SLIP_MAX = 28


def fortune_stick(request):
    fortune_slip_urls = {str(slip.order): slip.image.url for slip in FortuneSlip.objects.all()}
    return render(request, "happy_workplace/fortune_stick.html", {
        "fortune_slip_urls": fortune_slip_urls,
        "play": _play_state(request, "fortune"),
    })


def phone_analysis(request):
    return render(request, "happy_workplace/phone_analysis.html", {
        "play": _play_state(request, "phone_analysis"),
    })


GAME_LEADERBOARD_SIZE = 20
# game key -> (page label, highest score a real run can reach; anything above is rejected)
GAME_SCORE_RULES = {
    "squares": ("Squares", 200_000),
    "typing_th": ("พิมพ์เร็ว (ไทย)", 300),
    "typing_en": ("พิมพ์เร็ว (อังกฤษ)", 300),
}


def _game_leaderboard(game):
    return [
        {"name": s.name, "score": s.score, "detail": s.detail}
        for s in _best_per_name(GameScore.objects.filter(game=game), GAME_LEADERBOARD_SIZE)
    ]


def squares(request):
    settings_obj = SquaresSettings.get_solo()
    return render(request, "happy_workplace/squares.html", {
        "squares_settings": settings_obj,
        "squares_settings_json": {"sessionSeconds": settings_obj.session_minutes * 60},
        "settings_form": SquaresSettingsForm(instance=settings_obj),
        "leaderboard": _game_leaderboard("squares"),
        "word_count": SquaresWord.objects.count(),
        "play": _play_state(request, "squares"),
        "play_form": game_play_limit_form("squares")(instance=HappyWorkplaceSettings.get_solo()),
    })


def squares_puzzle(request):
    """Public JSON: one freshly generated puzzle (grid + hidden words)."""
    entries = list(SquaresWord.objects.values_list("word", "meaning", "category"))
    puzzle = generate_puzzle(entries)
    if not puzzle:
        return JsonResponse({"error": "คลังคำศัพท์ไม่พอสำหรับสร้างปริศนา"}, status=503)
    return JsonResponse(puzzle)


@login_required
@require_permission("happy_workplace.edit")
@require_POST
def squares_settings_update(request):
    form = SquaresSettingsForm(request.POST, instance=SquaresSettings.get_solo())
    if form.is_valid():
        form.save()
        messages.success(request, "บันทึกการตั้งค่าเกม Squares เรียบร้อยแล้ว")
    else:
        messages.error(request, "ค่าที่กรอกไม่ถูกต้อง (เวลา 1-60 นาที)")
    return redirect("happy_workplace:squares")


def typing_test(request):
    settings_obj = TypingSettings.get_solo()
    return render(request, "happy_workplace/typing_test.html", {
        "typing_settings": settings_obj,
        "typing_settings_json": {"sessionSeconds": settings_obj.session_minutes * 60},
        "settings_form": TypingSettingsForm(instance=settings_obj),
        "leaderboards": {g: _game_leaderboard(g) for g in ("typing_th", "typing_en")},
        "play": _play_state(request, "typing"),
        "play_form": game_play_limit_form("typing")(instance=HappyWorkplaceSettings.get_solo()),
    })


@login_required
@require_permission("happy_workplace.edit")
@require_POST
def typing_settings_update(request):
    form = TypingSettingsForm(request.POST, instance=TypingSettings.get_solo())
    if form.is_valid():
        form.save()
        messages.success(request, "บันทึกการตั้งค่าเกมพิมพ์เร็วเรียบร้อยแล้ว")
    else:
        messages.error(request, "ค่าที่กรอกไม่ถูกต้อง (เวลา 1-60 นาที)")
    return redirect("happy_workplace:typing_test")


@require_POST
def game_score_submit(request, game):
    """Public (players don't log in). Values are sanity-checked, but since
    scoring runs in the browser this can't fully stop a made-up score."""
    rule = GAME_SCORE_RULES.get(game)
    if not rule:
        return JsonResponse({"error": "unknown game"}, status=404)
    try:
        payload = json.loads(request.body)
        name = str(payload.get("name", "")).strip()[:25] or "ไม่ระบุชื่อ"
        score = int(payload["score"])
        detail = str(payload.get("detail", "")).strip()[:30]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"error": "invalid payload"}, status=400)
    if not (0 < score <= rule[1]):
        return JsonResponse({"error": "invalid score"}, status=400)
    same_name = [s for s in GameScore.objects.filter(game=game) if _name_key(s.name) == _name_key(name)]
    if not same_name:
        GameScore.objects.create(game=game, name=name, score=score, detail=detail)
    else:
        best = same_name[0]  # queryset is ordered best-first
        if score > best.score:
            best.name, best.score, best.detail = name, score, detail
            best.created_at = timezone.now()
            best.save()
        for extra in same_name[1:]:
            extra.delete()
    return JsonResponse({"leaderboard": _game_leaderboard(game)})


@login_required
@require_permission("happy_workplace.edit")
def game_scores_reset(request, game):
    rule = GAME_SCORE_RULES.get(game)
    if not rule:
        return redirect("happy_workplace:index")
    back = "happy_workplace:squares" if game == "squares" else "happy_workplace:typing_test"
    if request.method == "POST":
        GameScore.objects.filter(game=game).delete()
        messages.success(request, f"รีเซ็ตตารางคะแนน {rule[0]} เรียบร้อยแล้ว")
        return redirect(back)
    return render(request, "happy_workplace/game_scores_confirm_reset.html", {
        "game_label": rule[0],
        "score_count": GameScore.objects.filter(game=game).count(),
        "back_url_name": back,
    })


def dream(request):
    return render(request, "happy_workplace/dream.html", {
        "play": _play_state(request, "dream"),
    })


# ---------------------------------------------------------------------------
# Admin-only management — editing the announcements board / poster images
# requires login + happy_workplace.edit, same gating style as the rest of
# the app's create/edit/delete views.
# ---------------------------------------------------------------------------
@login_required
@require_permission("happy_workplace.edit")
def manage(request):
    return render(request, "happy_workplace/manage.html", {
        "announcements": Announcement.objects.all(),
        "posters": PosterImage.objects.all(),
        "fortune_slips": FortuneSlip.objects.all(),
        "squares_word_count": SquaresWord.objects.count(),
        "play_form": PlayLimitForm(instance=HappyWorkplaceSettings.get_solo()),
        "plays_today": GamePlay.objects.filter(day=timezone.localdate()).count(),
    })


@login_required
@require_permission("happy_workplace.edit")
def squares_words(request):
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("cat", "")
    qs = SquaresWord.objects.all()
    if cat in SquaresWord.Category.values:
        qs = qs.filter(category=cat)
    if q:
        qs = qs.filter(word__icontains=q) | qs.filter(meaning__icontains=q)
    return render(request, "happy_workplace/squares_words.html", {
        "words": qs.order_by("word"),
        "total": SquaresWord.objects.count(),
        "categories": SquaresWord.Category.choices,
        "q": q,
        "cat": cat,
    })


@login_required
@require_permission("happy_workplace.edit")
def squares_word_create(request):
    if request.method == "POST":
        form = SquaresWordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "เพิ่มคำศัพท์เรียบร้อยแล้ว")
            return redirect("happy_workplace:squares_words")
    else:
        form = SquaresWordForm()
    return render(request, "happy_workplace/squares_word_form.html", {"form": form, "is_new": True})


@login_required
@require_permission("happy_workplace.edit")
def squares_word_edit(request, pk):
    word = get_object_or_404(SquaresWord, pk=pk)
    if request.method == "POST":
        form = SquaresWordForm(request.POST, instance=word)
        if form.is_valid():
            form.save()
            messages.success(request, "แก้ไขคำศัพท์เรียบร้อยแล้ว")
            return redirect("happy_workplace:squares_words")
    else:
        form = SquaresWordForm(instance=word)
    return render(request, "happy_workplace/squares_word_form.html", {"form": form, "is_new": False})


@login_required
@require_permission("happy_workplace.edit")
def squares_word_delete(request, pk):
    word = get_object_or_404(SquaresWord, pk=pk)
    if request.method == "POST":
        word.delete()
        messages.success(request, "ลบคำศัพท์เรียบร้อยแล้ว")
        return redirect("happy_workplace:squares_words")
    return render(request, "happy_workplace/squares_word_confirm_delete.html", {"word": word})


@login_required
@require_permission("happy_workplace.edit")
def announcement_create(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "เพิ่มข่าวสารเรียบร้อยแล้ว")
            return redirect("happy_workplace:manage")
    else:
        form = AnnouncementForm()
    return render(request, "happy_workplace/announcement_form.html", {"form": form, "is_new": True})


@login_required
@require_permission("happy_workplace.edit")
def announcement_edit(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "แก้ไขข่าวสารเรียบร้อยแล้ว")
            return redirect("happy_workplace:manage")
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, "happy_workplace/announcement_form.html", {"form": form, "is_new": False})


@login_required
@require_permission("happy_workplace.edit")
def announcement_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        announcement.delete()
        messages.success(request, "ลบข่าวสารเรียบร้อยแล้ว")
        return redirect("happy_workplace:manage")
    return render(request, "happy_workplace/announcement_confirm_delete.html", {"announcement": announcement})


@login_required
@require_permission("happy_workplace.edit")
def poster_create(request):
    if request.method == "POST":
        form = PosterImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "เพิ่มภาพประกาศเรียบร้อยแล้ว")
            return redirect("happy_workplace:manage")
    else:
        form = PosterImageForm()
    return render(request, "happy_workplace/poster_form.html", {"form": form})


@login_required
@require_permission("happy_workplace.edit")
def poster_delete(request, pk):
    poster = get_object_or_404(PosterImage, pk=pk)
    if request.method == "POST":
        poster.delete()
        messages.success(request, "ลบภาพประกาศเรียบร้อยแล้ว")
        return redirect("happy_workplace:manage")
    return render(request, "happy_workplace/poster_confirm_delete.html", {"poster": poster})


@login_required
@require_permission("happy_workplace.edit")
def fortune_slip_create(request):
    """Bulk upload: the slip number comes from the last number in each
    file's name (p-12.jpg -> 12). Re-uploading a number replaces its image."""
    if request.method == "POST":
        form = FortuneSlipUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = form.cleaned_data["images"]
            fallback_number = form.cleaned_data["number"]
            saved, replaced, skipped = 0, 0, []
            for f in files:
                found = re.findall(r"\d+", os.path.splitext(f.name)[0])
                number = int(found[-1]) if found else (fallback_number if len(files) == 1 else None)
                if number is None or not (FORTUNE_SLIP_MIN <= number <= FORTUNE_SLIP_MAX):
                    skipped.append(f.name)
                    continue
                existing = FortuneSlip.objects.filter(order=number).first()
                if existing:
                    existing.image.delete(save=False)
                    existing.image = f
                    existing.save()
                    replaced += 1
                else:
                    FortuneSlip.objects.create(order=number, image=f)
                    saved += 1
            if saved or replaced:
                messages.success(request, f"อัปโหลดคำทำนายแล้ว: เพิ่มใหม่ {saved} ใบ, แทนที่ {replaced} ใบ")
            if skipped:
                messages.warning(
                    request,
                    "ข้ามไฟล์ที่หาเลขที่ใบ (1-28) จากชื่อไฟล์ไม่ได้: " + ", ".join(skipped),
                )
            return redirect("happy_workplace:fortune_slip_create" if not (saved or replaced) else "happy_workplace:manage")
    else:
        form = FortuneSlipUploadForm()
    uploaded = set(FortuneSlip.objects.values_list("order", flat=True))
    return render(request, "happy_workplace/fortune_slip_form.html", {
        "form": form,
        "uploaded_count": len(uploaded),
        "missing_numbers": [n for n in range(FORTUNE_SLIP_MIN, FORTUNE_SLIP_MAX + 1) if n not in uploaded],
        "total": FORTUNE_SLIP_MAX,
    })


@login_required
@require_permission("happy_workplace.edit")
def fortune_slip_delete(request, pk):
    slip = get_object_or_404(FortuneSlip, pk=pk)
    if request.method == "POST":
        slip.delete()
        messages.success(request, "ลบคำทำนายเรียบร้อยแล้ว")
        return redirect("happy_workplace:manage")
    return render(request, "happy_workplace/fortune_slip_confirm_delete.html", {"slip": slip})
