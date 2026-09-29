from django.urls import path

from . import views

app_name = "happy_workplace"

urlpatterns = [
    path("", views.index, name="index"),
    path("wordle/", views.wordle, name="wordle"),
    path("wordle/score/", views.wordle_submit_score, name="wordle_submit_score"),
    path("wordle/settings/", views.wordle_settings_update, name="wordle_settings_update"),
    path("wordle/reset/", views.wordle_reset_scores, name="wordle_reset_scores"),
    path("fortune-stick/", views.fortune_stick, name="fortune_stick"),
    path("phone-analysis/", views.phone_analysis, name="phone_analysis"),
    path("dream/", views.dream, name="dream"),
    path("squares/", views.squares, name="squares"),
    path("squares/puzzle/", views.squares_puzzle, name="squares_puzzle"),
    path("squares/settings/", views.squares_settings_update, name="squares_settings_update"),
    path("typing-test/", views.typing_test, name="typing_test"),
    path("typing-test/settings/", views.typing_settings_update, name="typing_settings_update"),
    path("game-score/<str:game>/", views.game_score_submit, name="game_score_submit"),
    path("game-score/<str:game>/reset/", views.game_scores_reset, name="game_scores_reset"),

    path("play/<str:game>/start/", views.play_start, name="play_start"),
    path("play/<str:game>/limit/", views.play_settings_update, name="play_game_limit_update"),

    path("manage/", views.manage, name="manage"),
    path("manage/play-limit/", views.play_settings_update, name="play_settings_update"),
    path("manage/play-limit/reset/", views.play_counts_reset, name="play_counts_reset"),
    path("manage/squares-words/", views.squares_words, name="squares_words"),
    path("manage/squares-words/new/", views.squares_word_create, name="squares_word_create"),
    path("manage/squares-words/<int:pk>/edit/", views.squares_word_edit, name="squares_word_edit"),
    path("manage/squares-words/<int:pk>/delete/", views.squares_word_delete, name="squares_word_delete"),
    path("manage/announcement/new/", views.announcement_create, name="announcement_create"),
    path("manage/announcement/<int:pk>/edit/", views.announcement_edit, name="announcement_edit"),
    path("manage/announcement/<int:pk>/delete/", views.announcement_delete, name="announcement_delete"),
    path("manage/poster/new/", views.poster_create, name="poster_create"),
    path("manage/poster/<int:pk>/delete/", views.poster_delete, name="poster_delete"),
    path("manage/fortune/new/", views.fortune_slip_create, name="fortune_slip_create"),
    path("manage/fortune/<int:pk>/delete/", views.fortune_slip_delete, name="fortune_slip_delete"),
]
