"""
Internationalization: string translations and language lookup.
"""
from __future__ import annotations

from typing import Any

LANG_DICT = {
"en": {
        # ── Core UX ──────────────────────────────────────────────────────────
        "start_prompt": "Please select your language / Vui lòng chọn ngôn ngữ:",
        "welcome": (
            "Welcome to TrackCredits.\n\n"
            "Send a track link or type a track name to fetch credits, lyrics, and streaming links."
        ),
        "help_txt": (
            "<b>How to use</b>\n\n"
            "Send a song title or a Spotify/YouTube/Apple Music link.\n"
            "Use /cancel to stop the current input flow.\n"
            "Use /top to see the contributor leaderboard.\n"
            "Use /lang to switch language.\n"
            "Inline mode: <code>@bot track_name</code>"
        ),
        "analyzing": "Analyzing track data...",
        "not_found": "Track not found.",
        "rate_limited": "You are sending requests too quickly. Please wait a few seconds.",
        "session_expired": "Session expired. Please send the track again.",
        "loaded": "Data loaded. Choose an option below.",
        "cache_hit": "Loaded from cache. Choose an option below.",
        "streams_title": "<b>Streaming platforms:</b>",
        "search_links": "<b>Fallback search links:</b>",
        "lyrics_title": "🎤 Lyrics",
        "no_lyrics": "<i>Lyrics are not available yet.</i>",
        "contrib_prompt": "What do you want to contribute?",
        "req_credits": "Send credits or track notes:",
        "req_lyrics1": "Step 1/2: Send the lyrics:",
        "req_lyrics2": "Step 2/2: Send the lyrics source / original author:",
        "req_report": "Describe the problem you found:",
        "submitted": "Submitted. Admin will review it soon.",
        "lyrics_already_exists": "This track already has lyrics from <b>{source}</b>.\nIf you'd like to contribute or correct them, please use the <b>Report</b> button.",
        "btn_view_song": "View Song",
        # ── Buttons ───────────────────────────────────────────────────────────
        "btn_streams": "Streams",
        "btn_credits": "Credits",
        "btn_lyrics": "Lyrics",
        "btn_contrib": "Contribute",
        "btn_report": "Report",
        "btn_wrong": "Wrong Track",
        "btn_back": "Back",
        "cancel_with_track": "Current action cancelled.",
        "cancel_no_track": "Cancelled. Send a song title or link to search.",
        "btn_continue_track": "Continue current track",
        "btn_new_search": "Search new track",
        "wrong_result": (
            "If the result is wrong, try again with <b>Song Title + Artist</b> "
            "or send a direct track link."
        ),
        # ── Input validation ──────────────────────────────────────────────────
        "access_denied": "Access denied.",
        "input_too_long": "Query too long. Please shorten it.",
        "url_extract_failed": (
            "Could not extract data from this link. "
            "Try a song title or a different link."
        ),
        "track_load_failed": "Could not load track data.",
        "content_too_long": "Content too long. Please shorten it and resubmit.",
        "promo_session_expired": "Session expired. Search for a track first.",
        # ── Leaderboard (/top) ────────────────────────────────────────────────
        "top_empty": "No contributors on the leaderboard yet.",
        "top_title": "🏆 <b>TrackCredits Contributor Leaderboard</b> — Page {page}",
        "top_prev": "Prev",
        "top_next": "Next",
        "top_footer": "Approved credits/lyrics = +5 pts · Bug report = +2 pts",
        # ── Admin panel ───────────────────────────────────────────────────────
        "metrics_empty": "<i>No metrics data yet.</i>",
        "admin_dashboard": (
            "<b>ADMIN DASHBOARD</b>\nPending: {count}\n\n"
            "Find a track first, then use /admin to add promo links."
        ),
        "admin_promo_title": "PROMO SETTINGS FOR:",
        "admin_btn_drums": "Add Drums + Bass link",
        "admin_btn_instrumental": "Add Instrumental link",
        "admin_btn_clear_promo": "Clear all promo links",
        "admin_promo_prompt": "ADMIN: Send YouTube link for the '{promo_type}' version (or /cancel).",
        "admin_promo_cleared": "All promo links for this track have been cleared.",
        "admin_invalid_request": "Invalid admin request.",
        "admin_sub_not_found": "Submission not found.",
        "admin_already_processed": "This submission has already been processed.",
        "admin_approved": "Approved {sub_type} for: {title}",
        "admin_rejected": "Rejected {sub_type} for: {title}",
        "user_contrib_approved": "Your {sub_type} contribution for <b>{title}</b> has been approved.",
        # ── Terms of Service ──────────────────────────────────────────────
        "terms_text": (
            "<b>📋 Terms of Service</b>\n\n"
            "By using TrackCredits Bot you agree to:\n"
            "• Use the bot for personal, non-commercial purposes only.\n"
            "• Not abuse rate limits or attempt to scrape data at scale.\n"
            "• Not submit false, misleading, or copyrighted content as contributions.\n"
            "• Accept that credits are non-refundable once purchased.\n\n"
            "The bot is provided as-is with no warranty. "
            "Service may be suspended for violation of these terms.\n\n"
            "<i>Last updated: 2025-01-01</i>"
        ),
        # ── Privacy Policy ────────────────────────────────────────────────
        "privacy_text": (
            "<b>🔒 Privacy Policy</b>\n\n"
            "<b>What we collect</b>\n"
            "• Your Telegram user ID and username (for credits and leaderboard).\n"
            "• Song searches and contribution history (for cache and analytics).\n"
            "• Credit transactions (for billing and dispute resolution).\n\n"
            "<b>What we do NOT collect</b>\n"
            "• Your real name, email, phone number, or payment card details.\n"
            "• Message content outside of bot interactions.\n\n"
            "<b>Data retention</b>\n"
            "Search cache: 14 days. User data: retained while you use the bot. "
            "Request deletion at any time via /cancel followed by contacting the admin.\n\n"
            "<b>Third-party services</b>\n"
            "Lyrics from Genius, lrclib.net, lyrics.ovh. "
            "Credits from MusicBrainz and YouTube. "
            "Platform links via Odesli.\n\n"
            "<i>Last updated: 2025-01-01</i>"
        ),
        # ── Contribution rejection notify ─────────────────────────────────
        "user_contrib_rejected": (
            "Your {sub_type} contribution for <b>{title}</b> was not approved this time.\n"
            "Feel free to try again with updated information!"
        ),
        # ── Buy / payment ─────────────────────────────────────────────────
        "buy_title": "💎 <b>Buy Credits</b>",
        "buy_balance": "Current balance: <b>{balance} credits</b>",
        "buy_provider_momo": "💳 Payment via MoMo",
        "buy_provider_stripe": "💳 Payment via Stripe (card)",
        "buy_provider_manual": "🏦 Manual bank transfer — admin confirms after payment",
        "buy_success": "🎉 <b>+{credits} credits</b> added!\nNew balance: <b>{balance}</b>.",
        "buy_error": "⚠️ Payment error. Please try again or contact the admin.",

        # ── Disambiguation ────────────────────────────────────────────────────
        "disambig_prompt": "🔎 <b>Multiple artists have '{query}'. Pick the right one:</b>",
        "disambig_none": "None of these",
        # ── Navigation callbacks ──────────────────────────────────────────────
        "invalid_page": "Invalid page.",
        "search_prompt": "Send a track link or title:",
        "invalid_choice": "Invalid choice.",
        "choice_expired": "This choice is no longer valid.",
        # ── Menu callbacks ────────────────────────────────────────────────────
        "searching_other_artists": "Searching for other artists with '{title}'...",
        "no_other_artists": (
            "No other artists found for <b>{title}</b>.\n\n"
            "Try sending a Spotify/YouTube link directly for a more accurate result."
        ),
        "lyrics_source_label": "Source: {source}",
        "community_desc_header": "\n\n📝 <b>Community description:</b>\n\n",
        "community_source_label": "\nSource: {source}",
        "community_contrib_label": "\nContributed by: @{contributor}",
        "credits_community_by": "\n\n<i>Community credits by: @{contributor}</i>",
        "view_on_genius": "View on Genius",
        "listen_on_spotify": "Listen on Spotify",
        # ── Credits rendering ─────────────────────────────────────────────────
        "credits_section_title": "<b>Original Song Credits:</b>",
        "credits_no_data": "<i>No original credits available.</i>",
        "credits_community_section": "\n📝 <b>Community description:</b>",
        "credits_rights": "\nAll original rights belong to {artist} and the respective creators.",
        # ── LRC / Synced lyrics ───────────────────────────────────────────────
        "btn_lrc": "⏱ Synced (.lrc)",
        "lrc_title": "Synced lyrics (.lrc)",
        # ── Admin: custom promo ───────────────────────────────────────────────
        "admin_btn_custom_promo": "➕ Custom type…",
        "admin_promo_name_prompt": "ADMIN: Type the custom promo type name (e.g. Karaoke), then send the YouTube link.",
    },
}


def t(key: str, context: Any) -> str:
    """Look up a translated string for the user's language (from Telegram context)."""
    user_data = getattr(context, "user_data", {}) or {}
    lang = user_data.get("lang", "en")
    return t_lang(key, lang)


def t_lang(key: str, lang: str) -> str:
    """Look up a translated string by explicit language code.

    Use this when no Telegram context is available (e.g. inside pure rendering
    functions like render_credits that receive a lang string instead of context).
    """
    return LANG_DICT.get(lang, LANG_DICT["en"]).get(key, f"[{key}]")

# ── Patch: inject 9 additional language blocks ────────────────────────────
_EXTRA_LANGS = {
"vi": {
    "start_prompt": "Vui lòng chọn ngôn ngữ:",
    "welcome": "Chào mừng đến với TrackCredits.\n\nGửi link bài hát hoặc nhập tên để xem credits, lời bài hát và link nghe nhạc.",
    "help_txt": "<b>Cách sử dụng</b>\n\nGửi tên bài hát hoặc link Spotify/YouTube/Apple Music.\nDùng /cancel để huỷ thao tác hiện tại.\nDùng /top để xem bảng xếp hạng đóng góp.\nDùng /lang để đổi ngôn ngữ.\nInline mode: <code>@bot tên_bài_hát</code>",
    "analyzing": "Đang phân tích dữ liệu bài hát...",
    "not_found": "Không tìm thấy bài hát.",
    "rate_limited": "Bạn gửi yêu cầu quá nhanh. Vui lòng chờ vài giây.",
    "session_expired": "Phiên đã hết hạn. Vui lòng gửi lại bài hát.",
    "loaded": "Đã tải dữ liệu. Chọn một tùy chọn bên dưới.",
    "cache_hit": "Tải từ bộ nhớ đệm. Chọn một tùy chọn bên dưới.",
    "streams_title": "<b>Nền tảng nghe nhạc:</b>",
    "search_links": "<b>Link tìm kiếm dự phòng:</b>",
    "lyrics_title": "🎤 Lời bài hát",
    "no_lyrics": "<i>Lời bài hát chưa có.</i>",
    "contrib_prompt": "Bạn muốn đóng góp gì?",
    "req_credits": "Gửi credits hoặc ghi chú về bài hát:",
    "req_lyrics1": "Bước 1/2: Gửi lời bài hát:",
    "req_lyrics2": "Bước 2/2: Gửi nguồn / tác giả gốc:",
    "req_report": "Mô tả vấn đề bạn phát hiện:",
    "submitted": "Đã gửi. Admin sẽ xem xét sớm.",
    "lyrics_already_exists": "Bài hát này đã có lời từ <b>{source}</b>.\nNếu muốn chỉnh sửa, hãy dùng nút <b>Báo lỗi</b>.",
    "btn_view_song": "Xem bài hát",
    "btn_streams": "Nghe nhạc",
    "btn_credits": "Credits",
    "btn_lyrics": "Lời bài hát",
    "btn_contrib": "Đóng góp",
    "btn_report": "Báo lỗi",
    "btn_wrong": "Sai bài hát",
    "btn_back": "Quay lại",
    "cancel_with_track": "Đã huỷ thao tác hiện tại.",
    "cancel_no_track": "Đã huỷ. Gửi tên hoặc link bài hát để tìm kiếm.",
    "btn_continue_track": "Tiếp tục bài hát hiện tại",
    "btn_new_search": "Tìm bài hát mới",
    "wrong_result": "Nếu kết quả sai, hãy thử lại với <b>Tên bài + Nghệ sĩ</b> hoặc gửi link trực tiếp.",
    "access_denied": "Truy cập bị từ chối.",
    "input_too_long": "Truy vấn quá dài. Vui lòng rút ngắn.",
    "url_extract_failed": "Không thể trích xuất dữ liệu từ link này. Thử tên bài hát hoặc link khác.",
    "track_load_failed": "Không thể tải dữ liệu bài hát.",
    "content_too_long": "Nội dung quá dài. Vui lòng rút ngắn và gửi lại.",
    "promo_session_expired": "Phiên đã hết hạn. Hãy tìm bài hát trước.",
    "top_empty": "Chưa có ai trong bảng xếp hạng.",
    "top_title": "🏆 <b>Bảng xếp hạng đóng góp TrackCredits</b> — Trang {page}",
    "top_prev": "Trước",
    "top_next": "Tiếp",
    "top_footer": "Credits/lời bài hát được duyệt = +5 điểm · Báo lỗi = +2 điểm",
    "metrics_empty": "<i>Chưa có dữ liệu thống kê.</i>",
    "admin_dashboard": "<b>TRANG QUẢN TRỊ</b>\nChờ duyệt: {count}\n\nTìm bài hát trước, sau đó dùng /admin để thêm link promo.",
    "admin_promo_title": "CÀI ĐẶT PROMO CHO:",
    "admin_btn_drums": "Thêm link Drums + Bass",
    "admin_btn_instrumental": "Thêm link Instrumental",
    "admin_btn_custom_promo": "➕ Loại tùy chỉnh…",
    "admin_btn_clear_promo": "Xoá tất cả link promo",
    "admin_promo_prompt": "ADMIN: Gửi link YouTube cho phiên bản '{promo_type}' (hoặc /cancel).",
    "admin_promo_name_prompt": "ADMIN: Nhập tên loại promo tùy chỉnh (ví dụ: Karaoke), sau đó gửi link YouTube.",
    "admin_promo_cleared": "Đã xoá tất cả link promo của bài hát này.",
    "admin_invalid_request": "Yêu cầu admin không hợp lệ.",
    "admin_sub_not_found": "Không tìm thấy bài gửi.",
    "admin_already_processed": "Bài gửi này đã được xử lý.",
    "admin_approved": "Đã duyệt {sub_type} cho: {title}",
    "admin_rejected": "Đã từ chối {sub_type} cho: {title}",
    "user_contrib_approved": "Đóng góp {sub_type} của bạn cho <b>{title}</b> đã được duyệt.",
    "disambig_prompt": "🔎 <b>Có nhiều nghệ sĩ tên '{query}'. Chọn đúng người:</b>",
    "disambig_none": "Không có ai",
    "invalid_page": "Trang không hợp lệ.",
    "search_prompt": "Gửi link hoặc tên bài hát:",
    "invalid_choice": "Lựa chọn không hợp lệ.",
    "choice_expired": "Lựa chọn này không còn hợp lệ.",
    "searching_other_artists": "Đang tìm nghệ sĩ khác có tên '{title}'...",
    "no_other_artists": "Không tìm thấy nghệ sĩ nào khác cho <b>{title}</b>.\n\nThử gửi link Spotify/YouTube trực tiếp để kết quả chính xác hơn.",
    "lyrics_source_label": "Nguồn: {source}",
    "community_desc_header": "\n\n📝 <b>Mô tả cộng đồng:</b>\n\n",
    "community_source_label": "\nNguồn: {source}",
    "community_contrib_label": "\nĐóng góp bởi: @{contributor}",
    "credits_community_by": "\n\n<i>Credits cộng đồng bởi: @{contributor}</i>",
    "view_on_genius": "Xem trên Genius",
    "listen_on_spotify": "Nghe trên Spotify",
    "credits_section_title": "<b>Credits bài hát gốc:</b>",
    "credits_no_data": "<i>Không có credits gốc.</i>",
    "credits_community_section": "\n📝 <b>Mô tả cộng đồng:</b>",
    "credits_rights": "\nTất cả bản quyền thuộc về {artist} và các tác giả liên quan.",
    "btn_lrc": "⏱ Có nhịp (.lrc)",
    "lrc_title": "Lời bài hát có nhịp (.lrc)",
},
"es": {
    "start_prompt": "Por favor selecciona tu idioma:",
    "welcome": "Bienvenido a TrackCredits.\n\nEnvía un enlace de canción o escribe un nombre para ver créditos, letras y enlaces de streaming.",
    "help_txt": "<b>Cómo usar</b>\n\nEnvía un título de canción o un enlace de Spotify/YouTube/Apple Music.\nUsa /cancel para detener el flujo actual.\nUsa /top para ver el ranking de colaboradores.\nUsa /lang para cambiar de idioma.\nModo inline: <code>@bot nombre_canción</code>",
    "analyzing": "Analizando datos de la canción...",
    "not_found": "Canción no encontrada.",
    "rate_limited": "Estás enviando solicitudes muy rápido. Espera unos segundos.",
    "session_expired": "Sesión expirada. Por favor envía la canción de nuevo.",
    "loaded": "Datos cargados. Elige una opción.",
    "cache_hit": "Cargado desde caché. Elige una opción.",
    "streams_title": "<b>Plataformas de streaming:</b>",
    "search_links": "<b>Enlaces de búsqueda alternativos:</b>",
    "lyrics_title": "🎤 Letra",
    "no_lyrics": "<i>La letra no está disponible aún.</i>",
    "contrib_prompt": "¿Qué quieres contribuir?",
    "req_credits": "Envía créditos o notas de la canción:",
    "req_lyrics1": "Paso 1/2: Envía la letra:",
    "req_lyrics2": "Paso 2/2: Envía la fuente / autor original:",
    "req_report": "Describe el problema que encontraste:",
    "submitted": "Enviado. El administrador lo revisará pronto.",
    "lyrics_already_exists": "Esta canción ya tiene letra de <b>{source}</b>.\nSi deseas corregirla, usa el botón <b>Reportar</b>.",
    "btn_view_song": "Ver canción",
    "btn_streams": "Streaming",
    "btn_credits": "Créditos",
    "btn_lyrics": "Letra",
    "btn_contrib": "Contribuir",
    "btn_report": "Reportar",
    "btn_wrong": "Canción incorrecta",
    "btn_back": "Volver",
    "cancel_with_track": "Acción actual cancelada.",
    "cancel_no_track": "Cancelado. Envía un título o enlace para buscar.",
    "btn_continue_track": "Continuar canción actual",
    "btn_new_search": "Buscar nueva canción",
    "wrong_result": "Si el resultado es incorrecto, intenta de nuevo con <b>Título + Artista</b> o envía un enlace directo.",
    "access_denied": "Acceso denegado.",
    "input_too_long": "Consulta demasiado larga. Acórtala.",
    "url_extract_failed": "No se pudo extraer datos de este enlace. Prueba con un título o enlace diferente.",
    "track_load_failed": "No se pudo cargar los datos de la canción.",
    "content_too_long": "Contenido demasiado largo. Acórtalo y reenvía.",
    "promo_session_expired": "Sesión expirada. Busca una canción primero.",
    "top_empty": "No hay colaboradores en el ranking aún.",
    "top_title": "🏆 <b>Ranking de colaboradores de TrackCredits</b> — Página {page}",
    "top_prev": "Anterior",
    "top_next": "Siguiente",
    "top_footer": "Créditos/letra aprobados = +5 pts · Reporte = +2 pts",
    "metrics_empty": "<i>Sin datos de métricas aún.</i>",
    "admin_dashboard": "<b>PANEL ADMIN</b>\nPendientes: {count}\n\nBusca una canción primero, luego usa /admin para agregar links promo.",
    "admin_promo_title": "CONFIGURACIÓN PROMO PARA:",
    "admin_btn_drums": "Agregar link Drums + Bass",
    "admin_btn_instrumental": "Agregar link Instrumental",
    "admin_btn_custom_promo": "➕ Tipo personalizado…",
    "admin_btn_clear_promo": "Limpiar todos los links promo",
    "admin_promo_prompt": "ADMIN: Envía el link de YouTube para la versión '{promo_type}' (o /cancel).",
    "admin_promo_name_prompt": "ADMIN: Escribe el nombre del tipo promo personalizado (ej. Karaoke), luego envía el link de YouTube.",
    "admin_promo_cleared": "Todos los links promo de esta canción han sido eliminados.",
    "admin_invalid_request": "Solicitud admin inválida.",
    "admin_sub_not_found": "Envío no encontrado.",
    "admin_already_processed": "Este envío ya fue procesado.",
    "admin_approved": "Aprobado {sub_type} para: {title}",
    "admin_rejected": "Rechazado {sub_type} para: {title}",
    "user_contrib_approved": "Tu contribución {sub_type} para <b>{title}</b> fue aprobada.",
    "disambig_prompt": "🔎 <b>Varios artistas tienen '{query}'. Elige el correcto:</b>",
    "disambig_none": "Ninguno de estos",
    "invalid_page": "Página inválida.",
    "search_prompt": "Envía un enlace o título de canción:",
    "invalid_choice": "Opción inválida.",
    "choice_expired": "Esta opción ya no es válida.",
    "searching_other_artists": "Buscando otros artistas con '{title}'...",
    "no_other_artists": "No se encontraron otros artistas para <b>{title}</b>.\n\nIntenta enviar un enlace de Spotify/YouTube directamente.",
    "lyrics_source_label": "Fuente: {source}",
    "community_desc_header": "\n\n📝 <b>Descripción de la comunidad:</b>\n\n",
    "community_source_label": "\nFuente: {source}",
    "community_contrib_label": "\nContribuido por: @{contributor}",
    "credits_community_by": "\n\n<i>Créditos de la comunidad por: @{contributor}</i>",
    "view_on_genius": "Ver en Genius",
    "listen_on_spotify": "Escuchar en Spotify",
    "credits_section_title": "<b>Créditos originales de la canción:</b>",
    "credits_no_data": "<i>Sin créditos originales disponibles.</i>",
    "credits_community_section": "\n📝 <b>Descripción de la comunidad:</b>",
    "credits_rights": "\nTodos los derechos originales pertenecen a {artist} y los creadores respectivos.",
    "btn_lrc": "⏱ Sincronizado (.lrc)",
    "lrc_title": "Letra sincronizada (.lrc)",
},
"pt": {
    "start_prompt": "Por favor selecione seu idioma:",
    "welcome": "Bem-vindo ao TrackCredits.\n\nEnvie um link de música ou digite um nome para ver créditos, letras e links de streaming.",
    "help_txt": "<b>Como usar</b>\n\nEnvie um título de música ou link do Spotify/YouTube/Apple Music.\nUse /cancel para cancelar o fluxo atual.\nUse /top para ver o ranking de colaboradores.\nUse /lang para mudar de idioma.\nModo inline: <code>@bot nome_música</code>",
    "analyzing": "Analisando dados da música...",
    "not_found": "Música não encontrada.",
    "rate_limited": "Você está enviando solicitações muito rápido. Aguarde alguns segundos.",
    "session_expired": "Sessão expirada. Envie a música novamente.",
    "loaded": "Dados carregados. Escolha uma opção abaixo.",
    "cache_hit": "Carregado do cache. Escolha uma opção abaixo.",
    "streams_title": "<b>Plataformas de streaming:</b>",
    "search_links": "<b>Links de busca alternativos:</b>",
    "lyrics_title": "🎤 Letra",
    "no_lyrics": "<i>A letra ainda não está disponível.</i>",
    "contrib_prompt": "O que você quer contribuir?",
    "req_credits": "Envie créditos ou notas sobre a música:",
    "req_lyrics1": "Passo 1/2: Envie a letra:",
    "req_lyrics2": "Passo 2/2: Envie a fonte / autor original:",
    "req_report": "Descreva o problema encontrado:",
    "submitted": "Enviado. O admin revisará em breve.",
    "lyrics_already_exists": "Esta música já tem letra de <b>{source}</b>.\nSe quiser corrigir, use o botão <b>Reportar</b>.",
    "btn_view_song": "Ver música",
    "btn_streams": "Streaming",
    "btn_credits": "Créditos",
    "btn_lyrics": "Letra",
    "btn_contrib": "Contribuir",
    "btn_report": "Reportar",
    "btn_wrong": "Música errada",
    "btn_back": "Voltar",
    "cancel_with_track": "Ação atual cancelada.",
    "cancel_no_track": "Cancelado. Envie um título ou link para buscar.",
    "btn_continue_track": "Continuar música atual",
    "btn_new_search": "Buscar nova música",
    "wrong_result": "Se o resultado estiver errado, tente novamente com <b>Título + Artista</b> ou envie um link direto.",
    "access_denied": "Acesso negado.",
    "input_too_long": "Consulta muito longa. Por favor encurte.",
    "url_extract_failed": "Não foi possível extrair dados deste link. Tente um título ou link diferente.",
    "track_load_failed": "Não foi possível carregar os dados da música.",
    "content_too_long": "Conteúdo muito longo. Por favor encurte e reenvie.",
    "promo_session_expired": "Sessão expirada. Busque uma música primeiro.",
    "top_empty": "Nenhum colaborador no ranking ainda.",
    "top_title": "🏆 <b>Ranking de colaboradores do TrackCredits</b> — Página {page}",
    "top_prev": "Anterior",
    "top_next": "Próximo",
    "top_footer": "Créditos/letra aprovados = +5 pts · Relatório = +2 pts",
    "metrics_empty": "<i>Sem dados de métricas ainda.</i>",
    "admin_dashboard": "<b>PAINEL ADMIN</b>\nPendentes: {count}\n\nBusque uma música primeiro, depois use /admin para adicionar links promo.",
    "admin_promo_title": "CONFIG PROMO PARA:",
    "admin_btn_drums": "Adicionar link Drums + Bass",
    "admin_btn_instrumental": "Adicionar link Instrumental",
    "admin_btn_custom_promo": "➕ Tipo personalizado…",
    "admin_btn_clear_promo": "Limpar todos os links promo",
    "admin_promo_prompt": "ADMIN: Envie o link do YouTube para a versão '{promo_type}' (ou /cancel).",
    "admin_promo_name_prompt": "ADMIN: Digite o nome do tipo promo personalizado (ex. Karaoke), depois envie o link do YouTube.",
    "admin_promo_cleared": "Todos os links promo desta música foram removidos.",
    "admin_invalid_request": "Solicitação admin inválida.",
    "admin_sub_not_found": "Envio não encontrado.",
    "admin_already_processed": "Este envio já foi processado.",
    "admin_approved": "Aprovado {sub_type} para: {title}",
    "admin_rejected": "Rejeitado {sub_type} para: {title}",
    "user_contrib_approved": "Sua contribuição {sub_type} para <b>{title}</b> foi aprovada.",
    "disambig_prompt": "🔎 <b>Vários artistas têm '{query}'. Escolha o correto:</b>",
    "disambig_none": "Nenhum destes",
    "invalid_page": "Página inválida.",
    "search_prompt": "Envie um link ou título de música:",
    "invalid_choice": "Escolha inválida.",
    "choice_expired": "Esta escolha não é mais válida.",
    "searching_other_artists": "Buscando outros artistas com '{title}'...",
    "no_other_artists": "Nenhum outro artista encontrado para <b>{title}</b>.\n\nTente enviar um link do Spotify/YouTube diretamente.",
    "lyrics_source_label": "Fonte: {source}",
    "community_desc_header": "\n\n📝 <b>Descrição da comunidade:</b>\n\n",
    "community_source_label": "\nFonte: {source}",
    "community_contrib_label": "\nContribuído por: @{contributor}",
    "credits_community_by": "\n\n<i>Créditos da comunidade por: @{contributor}</i>",
    "view_on_genius": "Ver no Genius",
    "listen_on_spotify": "Ouvir no Spotify",
    "credits_section_title": "<b>Créditos originais da música:</b>",
    "credits_no_data": "<i>Sem créditos originais disponíveis.</i>",
    "credits_community_section": "\n📝 <b>Descrição da comunidade:</b>",
    "credits_rights": "\nTodos os direitos originais pertencem a {artist} e aos respectivos criadores.",
    "btn_lrc": "⏱ Sincronizado (.lrc)",
    "lrc_title": "Letra sincronizada (.lrc)",
},
"fr": {
    "start_prompt": "Veuillez sélectionner votre langue :",
    "welcome": "Bienvenue sur TrackCredits.\n\nEnvoyez un lien de chanson ou tapez un nom pour voir les crédits, paroles et liens de streaming.",
    "help_txt": "<b>Comment utiliser</b>\n\nEnvoyez un titre de chanson ou un lien Spotify/YouTube/Apple Music.\nUtilisez /cancel pour annuler l'action en cours.\nUtilisez /top pour voir le classement des contributeurs.\nUtilisez /lang pour changer de langue.\nMode inline : <code>@bot nom_chanson</code>",
    "analyzing": "Analyse des données de la chanson...",
    "not_found": "Chanson introuvable.",
    "rate_limited": "Vous envoyez des requêtes trop vite. Veuillez patienter quelques secondes.",
    "session_expired": "Session expirée. Veuillez renvoyer la chanson.",
    "loaded": "Données chargées. Choisissez une option.",
    "cache_hit": "Chargé depuis le cache. Choisissez une option.",
    "streams_title": "<b>Plateformes de streaming :</b>",
    "search_links": "<b>Liens de recherche alternatifs :</b>",
    "lyrics_title": "🎤 Paroles",
    "no_lyrics": "<i>Les paroles ne sont pas encore disponibles.</i>",
    "contrib_prompt": "Que souhaitez-vous contribuer ?",
    "req_credits": "Envoyez les crédits ou des notes sur la chanson :",
    "req_lyrics1": "Étape 1/2 : Envoyez les paroles :",
    "req_lyrics2": "Étape 2/2 : Envoyez la source / l'auteur original :",
    "req_report": "Décrivez le problème que vous avez trouvé :",
    "submitted": "Soumis. L'administrateur examinera cela bientôt.",
    "lyrics_already_exists": "Cette chanson a déjà des paroles de <b>{source}</b>.\nSi vous souhaitez les corriger, utilisez le bouton <b>Signaler</b>.",
    "btn_view_song": "Voir la chanson",
    "btn_streams": "Streaming",
    "btn_credits": "Crédits",
    "btn_lyrics": "Paroles",
    "btn_contrib": "Contribuer",
    "btn_report": "Signaler",
    "btn_wrong": "Mauvaise chanson",
    "btn_back": "Retour",
    "cancel_with_track": "Action en cours annulée.",
    "cancel_no_track": "Annulé. Envoyez un titre ou un lien pour rechercher.",
    "btn_continue_track": "Continuer la chanson actuelle",
    "btn_new_search": "Rechercher une nouvelle chanson",
    "wrong_result": "Si le résultat est incorrect, réessayez avec <b>Titre + Artiste</b> ou envoyez un lien direct.",
    "access_denied": "Accès refusé.",
    "input_too_long": "Requête trop longue. Veuillez la raccourcir.",
    "url_extract_failed": "Impossible d'extraire des données de ce lien. Essayez un titre ou un autre lien.",
    "track_load_failed": "Impossible de charger les données de la chanson.",
    "content_too_long": "Contenu trop long. Veuillez le raccourcir et le renvoyer.",
    "promo_session_expired": "Session expirée. Recherchez d'abord une chanson.",
    "top_empty": "Aucun contributeur dans le classement pour l'instant.",
    "top_title": "🏆 <b>Classement des contributeurs TrackCredits</b> — Page {page}",
    "top_prev": "Précédent",
    "top_next": "Suivant",
    "top_footer": "Crédits/paroles approuvés = +5 pts · Signalement = +2 pts",
    "metrics_empty": "<i>Aucune donnée de métriques pour l'instant.</i>",
    "admin_dashboard": "<b>TABLEAU DE BORD ADMIN</b>\nEn attente : {count}\n\nTrouvez d'abord une chanson, puis utilisez /admin pour ajouter des liens promo.",
    "admin_promo_title": "PARAMÈTRES PROMO POUR :",
    "admin_btn_drums": "Ajouter lien Drums + Bass",
    "admin_btn_instrumental": "Ajouter lien Instrumental",
    "admin_btn_custom_promo": "➕ Type personnalisé…",
    "admin_btn_clear_promo": "Effacer tous les liens promo",
    "admin_promo_prompt": "ADMIN : Envoyez le lien YouTube pour la version '{promo_type}' (ou /cancel).",
    "admin_promo_name_prompt": "ADMIN : Tapez le nom du type promo personnalisé (ex. Karaoké), puis envoyez le lien YouTube.",
    "admin_promo_cleared": "Tous les liens promo de cette chanson ont été supprimés.",
    "admin_invalid_request": "Requête admin invalide.",
    "admin_sub_not_found": "Soumission introuvable.",
    "admin_already_processed": "Cette soumission a déjà été traitée.",
    "admin_approved": "{sub_type} approuvé pour : {title}",
    "admin_rejected": "{sub_type} rejeté pour : {title}",
    "user_contrib_approved": "Votre contribution {sub_type} pour <b>{title}</b> a été approuvée.",
    "disambig_prompt": "🔎 <b>Plusieurs artistes ont '{query}'. Choisissez le bon :</b>",
    "disambig_none": "Aucun de ceux-ci",
    "invalid_page": "Page invalide.",
    "search_prompt": "Envoyez un lien ou un titre de chanson :",
    "invalid_choice": "Choix invalide.",
    "choice_expired": "Ce choix n'est plus valide.",
    "searching_other_artists": "Recherche d'autres artistes avec '{title}'...",
    "no_other_artists": "Aucun autre artiste trouvé pour <b>{title}</b>.\n\nEssayez d'envoyer un lien Spotify/YouTube directement.",
    "lyrics_source_label": "Source : {source}",
    "community_desc_header": "\n\n📝 <b>Description de la communauté :</b>\n\n",
    "community_source_label": "\nSource : {source}",
    "community_contrib_label": "\nContribué par : @{contributor}",
    "credits_community_by": "\n\n<i>Crédits de la communauté par : @{contributor}</i>",
    "view_on_genius": "Voir sur Genius",
    "listen_on_spotify": "Écouter sur Spotify",
    "credits_section_title": "<b>Crédits originaux de la chanson :</b>",
    "credits_no_data": "<i>Aucun crédit original disponible.</i>",
    "credits_community_section": "\n📝 <b>Description de la communauté :</b>",
    "credits_rights": "\nTous les droits originaux appartiennent à {artist} et aux créateurs respectifs.",
    "btn_lrc": "⏱ Synchronisé (.lrc)",
    "lrc_title": "Paroles synchronisées (.lrc)",
},
"ru": {
    "start_prompt": "Пожалуйста, выберите язык:",
    "welcome": "Добро пожаловать в TrackCredits.\n\nОтправьте ссылку на трек или введите название, чтобы увидеть credits, текст и ссылки на стриминг.",
    "help_txt": "<b>Как пользоваться</b>\n\nОтправьте название песни или ссылку на Spotify/YouTube/Apple Music.\nИспользуйте /cancel для отмены текущего действия.\nИспользуйте /top для просмотра рейтинга участников.\nИспользуйте /lang для смены языка.\nInline-режим: <code>@bot название_трека</code>",
    "analyzing": "Анализ данных трека...",
    "not_found": "Трек не найден.",
    "rate_limited": "Вы отправляете запросы слишком быстро. Подождите несколько секунд.",
    "session_expired": "Сессия истекла. Пожалуйста, отправьте трек снова.",
    "loaded": "Данные загружены. Выберите опцию.",
    "cache_hit": "Загружено из кэша. Выберите опцию.",
    "streams_title": "<b>Стриминговые платформы:</b>",
    "search_links": "<b>Резервные ссылки поиска:</b>",
    "lyrics_title": "🎤 Текст",
    "no_lyrics": "<i>Текст песни пока недоступен.</i>",
    "contrib_prompt": "Что вы хотите добавить?",
    "req_credits": "Отправьте credits или заметки о треке:",
    "req_lyrics1": "Шаг 1/2: Отправьте текст песни:",
    "req_lyrics2": "Шаг 2/2: Отправьте источник / оригинального автора:",
    "req_report": "Опишите найденную проблему:",
    "submitted": "Отправлено. Администратор скоро проверит.",
    "lyrics_already_exists": "У этого трека уже есть текст от <b>{source}</b>.\nЕсли хотите исправить, используйте кнопку <b>Сообщить</b>.",
    "btn_view_song": "Посмотреть песню",
    "btn_streams": "Стриминг",
    "btn_credits": "Credits",
    "btn_lyrics": "Текст",
    "btn_contrib": "Добавить",
    "btn_report": "Сообщить",
    "btn_wrong": "Неверный трек",
    "btn_back": "Назад",
    "cancel_with_track": "Текущее действие отменено.",
    "cancel_no_track": "Отменено. Отправьте название или ссылку для поиска.",
    "btn_continue_track": "Продолжить текущий трек",
    "btn_new_search": "Найти новый трек",
    "wrong_result": "Если результат неверный, попробуйте снова с <b>Название + Исполнитель</b> или отправьте прямую ссылку.",
    "access_denied": "Доступ запрещён.",
    "input_too_long": "Запрос слишком длинный. Пожалуйста, сократите.",
    "url_extract_failed": "Не удалось извлечь данные из этой ссылки. Попробуйте название или другую ссылку.",
    "track_load_failed": "Не удалось загрузить данные трека.",
    "content_too_long": "Содержимое слишком длинное. Сократите и отправьте снова.",
    "promo_session_expired": "Сессия истекла. Сначала найдите трек.",
    "top_empty": "Пока нет участников в рейтинге.",
    "top_title": "🏆 <b>Рейтинг участников TrackCredits</b> — Страница {page}",
    "top_prev": "Назад",
    "top_next": "Вперёд",
    "top_footer": "Одобренные credits/текст = +5 pts · Репорт = +2 pts",
    "metrics_empty": "<i>Данных метрик пока нет.</i>",
    "admin_dashboard": "<b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>\nОжидает: {count}\n\nСначала найдите трек, затем используйте /admin для добавления promo-ссылок.",
    "admin_promo_title": "НАСТРОЙКИ PROMO ДЛЯ:",
    "admin_btn_drums": "Добавить ссылку Drums + Bass",
    "admin_btn_instrumental": "Добавить ссылку Instrumental",
    "admin_btn_custom_promo": "➕ Свой тип…",
    "admin_btn_clear_promo": "Очистить все promo-ссылки",
    "admin_promo_prompt": "ADMIN: Отправьте ссылку YouTube для версии '{promo_type}' (или /cancel).",
    "admin_promo_name_prompt": "ADMIN: Введите название своего типа promo (например, Karaoke), затем отправьте ссылку YouTube.",
    "admin_promo_cleared": "Все promo-ссылки для этого трека очищены.",
    "admin_invalid_request": "Неверный запрос администратора.",
    "admin_sub_not_found": "Отправка не найдена.",
    "admin_already_processed": "Эта отправка уже обработана.",
    "admin_approved": "Одобрено {sub_type} для: {title}",
    "admin_rejected": "Отклонено {sub_type} для: {title}",
    "user_contrib_approved": "Ваш вклад {sub_type} для <b>{title}</b> одобрен.",
    "disambig_prompt": "🔎 <b>Несколько артистов с именем '{query}'. Выберите нужного:</b>",
    "disambig_none": "Никто из них",
    "invalid_page": "Недопустимая страница.",
    "search_prompt": "Отправьте ссылку или название трека:",
    "invalid_choice": "Неверный выбор.",
    "choice_expired": "Этот выбор больше недействителен.",
    "searching_other_artists": "Поиск других артистов с '{title}'...",
    "no_other_artists": "Другие артисты для <b>{title}</b> не найдены.\n\nПопробуйте отправить ссылку Spotify/YouTube напрямую.",
    "lyrics_source_label": "Источник: {source}",
    "community_desc_header": "\n\n📝 <b>Описание сообщества:</b>\n\n",
    "community_source_label": "\nИсточник: {source}",
    "community_contrib_label": "\nДобавлено пользователем: @{contributor}",
    "credits_community_by": "\n\n<i>Credits сообщества от: @{contributor}</i>",
    "view_on_genius": "Смотреть на Genius",
    "listen_on_spotify": "Слушать на Spotify",
    "credits_section_title": "<b>Оригинальные credits трека:</b>",
    "credits_no_data": "<i>Оригинальные credits недоступны.</i>",
    "credits_community_section": "\n📝 <b>Описание сообщества:</b>",
    "credits_rights": "\nВсе оригинальные права принадлежат {artist} и соответствующим создателям.",
    "btn_lrc": "⏱ Синхронизировано (.lrc)",
    "lrc_title": "Синхронизированный текст (.lrc)",
},
"ko": {
    "start_prompt": "언어를 선택하세요:",
    "welcome": "TrackCredits에 오신 것을 환영합니다.\n\n곡 링크를 보내거나 제목을 입력하면 크레딧, 가사, 스트리밍 링크를 확인할 수 있습니다.",
    "help_txt": "<b>사용 방법</b>\n\n곡 제목 또는 Spotify/YouTube/Apple Music 링크를 보내세요.\n현재 작업을 취소하려면 /cancel을 사용하세요.\n기여자 순위를 보려면 /top을 사용하세요.\n언어를 변경하려면 /lang을 사용하세요.\n인라인 모드: <code>@bot 곡 이름</code>",
    "analyzing": "트랙 데이터 분석 중...",
    "not_found": "트랙을 찾을 수 없습니다.",
    "rate_limited": "요청을 너무 빠르게 보내고 있습니다. 잠시 기다려 주세요.",
    "session_expired": "세션이 만료되었습니다. 트랙을 다시 보내 주세요.",
    "loaded": "데이터가 로드되었습니다. 옵션을 선택하세요.",
    "cache_hit": "캐시에서 로드되었습니다. 옵션을 선택하세요.",
    "streams_title": "<b>스트리밍 플랫폼:</b>",
    "search_links": "<b>대체 검색 링크:</b>",
    "lyrics_title": "🎤 가사",
    "no_lyrics": "<i>아직 가사가 없습니다.</i>",
    "contrib_prompt": "무엇을 기여하시겠습니까?",
    "req_credits": "크레딧 또는 트랙 메모를 보내세요:",
    "req_lyrics1": "1단계/2: 가사를 보내세요:",
    "req_lyrics2": "2단계/2: 가사 출처 / 원작자를 보내세요:",
    "req_report": "발견한 문제를 설명하세요:",
    "submitted": "제출되었습니다. 관리자가 곧 검토합니다.",
    "lyrics_already_exists": "이 트랙은 이미 <b>{source}</b>에서 가사가 있습니다.\n수정하려면 <b>신고</b> 버튼을 사용하세요.",
    "btn_view_song": "곡 보기",
    "btn_streams": "스트리밍",
    "btn_credits": "크레딧",
    "btn_lyrics": "가사",
    "btn_contrib": "기여",
    "btn_report": "신고",
    "btn_wrong": "잘못된 트랙",
    "btn_back": "뒤로",
    "cancel_with_track": "현재 작업이 취소되었습니다.",
    "cancel_no_track": "취소되었습니다. 제목 또는 링크를 보내서 검색하세요.",
    "btn_continue_track": "현재 트랙 계속",
    "btn_new_search": "새 트랙 검색",
    "wrong_result": "결과가 잘못된 경우 <b>곡 제목 + 아티스트</b>로 다시 시도하거나 직접 링크를 보내세요.",
    "access_denied": "접근이 거부되었습니다.",
    "input_too_long": "쿼리가 너무 깁니다. 줄여 주세요.",
    "url_extract_failed": "이 링크에서 데이터를 추출할 수 없습니다. 곡 제목이나 다른 링크를 시도하세요.",
    "track_load_failed": "트랙 데이터를 로드할 수 없습니다.",
    "content_too_long": "내용이 너무 깁니다. 줄여서 다시 제출하세요.",
    "promo_session_expired": "세션이 만료되었습니다. 먼저 트랙을 검색하세요.",
    "top_empty": "아직 순위에 기여자가 없습니다.",
    "top_title": "🏆 <b>TrackCredits 기여자 순위</b> — {page}페이지",
    "top_prev": "이전",
    "top_next": "다음",
    "top_footer": "승인된 크레딧/가사 = +5점 · 버그 신고 = +2점",
    "metrics_empty": "<i>아직 지표 데이터가 없습니다.</i>",
    "admin_dashboard": "<b>관리자 대시보드</b>\n대기 중: {count}\n\n먼저 트랙을 찾은 다음 /admin을 사용하여 프로모 링크를 추가하세요.",
    "admin_promo_title": "프로모 설정:",
    "admin_btn_drums": "Drums + Bass 링크 추가",
    "admin_btn_instrumental": "Instrumental 링크 추가",
    "admin_btn_custom_promo": "➕ 커스텀 유형…",
    "admin_btn_clear_promo": "모든 프로모 링크 삭제",
    "admin_promo_prompt": "ADMIN: '{promo_type}' 버전의 YouTube 링크를 보내세요 (또는 /cancel).",
    "admin_promo_name_prompt": "ADMIN: 커스텀 프로모 유형 이름을 입력하세요 (예: 노래방), 그런 다음 YouTube 링크를 보내세요.",
    "admin_promo_cleared": "이 트랙의 모든 프로모 링크가 삭제되었습니다.",
    "admin_invalid_request": "잘못된 관리자 요청입니다.",
    "admin_sub_not_found": "제출물을 찾을 수 없습니다.",
    "admin_already_processed": "이 제출물은 이미 처리되었습니다.",
    "admin_approved": "{title}의 {sub_type} 승인됨",
    "admin_rejected": "{title}의 {sub_type} 거부됨",
    "user_contrib_approved": "<b>{title}</b>에 대한 {sub_type} 기여가 승인되었습니다.",
    "disambig_prompt": "🔎 <b>'{query}'라는 아티스트가 여러 명입니다. 올바른 분을 선택하세요:</b>",
    "disambig_none": "해당 없음",
    "invalid_page": "유효하지 않은 페이지입니다.",
    "search_prompt": "트랙 링크 또는 제목을 보내세요:",
    "invalid_choice": "유효하지 않은 선택입니다.",
    "choice_expired": "이 선택은 더 이상 유효하지 않습니다.",
    "searching_other_artists": "'{title}'의 다른 아티스트를 검색 중...",
    "no_other_artists": "<b>{title}</b>에 대한 다른 아티스트를 찾을 수 없습니다.\n\nSpotify/YouTube 링크를 직접 보내 보세요.",
    "lyrics_source_label": "출처: {source}",
    "community_desc_header": "\n\n📝 <b>커뮤니티 설명:</b>\n\n",
    "community_source_label": "\n출처: {source}",
    "community_contrib_label": "\n제공자: @{contributor}",
    "credits_community_by": "\n\n<i>커뮤니티 크레딧 제공: @{contributor}</i>",
    "view_on_genius": "Genius에서 보기",
    "listen_on_spotify": "Spotify에서 듣기",
    "credits_section_title": "<b>원곡 크레딧:</b>",
    "credits_no_data": "<i>원곡 크레딧이 없습니다.</i>",
    "credits_community_section": "\n📝 <b>커뮤니티 설명:</b>",
    "credits_rights": "\n모든 원곡 권리는 {artist} 및 각 창작자에게 있습니다.",
    "btn_lrc": "⏱ 동기화 (.lrc)",
    "lrc_title": "동기화 가사 (.lrc)",
},
"ja": {
    "start_prompt": "言語を選択してください：",
    "welcome": "TrackCreditsへようこそ。\n\n曲のリンクまたは名前を送ると、クレジット、歌詞、ストリーミングリンクを取得できます。",
    "help_txt": "<b>使い方</b>\n\n曲のタイトルまたはSpotify/YouTube/Apple Musicのリンクを送ってください。\n/cancelで現在の操作をキャンセル。\n/topで貢献者ランキングを表示。\n/langで言語を変更。\nインラインモード：<code>@bot 曲名</code>",
    "analyzing": "トラックデータを分析中...",
    "not_found": "トラックが見つかりません。",
    "rate_limited": "リクエストが多すぎます。数秒お待ちください。",
    "session_expired": "セッションが切れました。もう一度トラックを送ってください。",
    "loaded": "データを読み込みました。オプションを選択してください。",
    "cache_hit": "キャッシュから読み込みました。オプションを選択してください。",
    "streams_title": "<b>ストリーミングプラットフォーム：</b>",
    "search_links": "<b>代替検索リンク：</b>",
    "lyrics_title": "🎤 歌詞",
    "no_lyrics": "<i>歌詞はまだ利用できません。</i>",
    "contrib_prompt": "何を投稿しますか？",
    "req_credits": "クレジットまたはトラックメモを送ってください：",
    "req_lyrics1": "ステップ1/2：歌詞を送ってください：",
    "req_lyrics2": "ステップ2/2：出典 / 原作者を送ってください：",
    "req_report": "見つけた問題を説明してください：",
    "submitted": "送信されました。管理者が間もなく確認します。",
    "lyrics_already_exists": "このトラックには既に<b>{source}</b>からの歌詞があります。\n修正したい場合は<b>報告</b>ボタンを使用してください。",
    "btn_view_song": "曲を見る",
    "btn_streams": "ストリーミング",
    "btn_credits": "クレジット",
    "btn_lyrics": "歌詞",
    "btn_contrib": "投稿",
    "btn_report": "報告",
    "btn_wrong": "間違ったトラック",
    "btn_back": "戻る",
    "cancel_with_track": "現在の操作をキャンセルしました。",
    "cancel_no_track": "キャンセルしました。曲のタイトルまたはリンクを送って検索してください。",
    "btn_continue_track": "現在のトラックを続ける",
    "btn_new_search": "新しいトラックを検索",
    "wrong_result": "結果が間違っている場合は、<b>曲名 + アーティスト</b>で再試行するか、直接リンクを送ってください。",
    "access_denied": "アクセス拒否。",
    "input_too_long": "クエリが長すぎます。短くしてください。",
    "url_extract_failed": "このリンクからデータを抽出できません。曲名または別のリンクをお試しください。",
    "track_load_failed": "トラックデータを読み込めませんでした。",
    "content_too_long": "内容が長すぎます。短くして再送してください。",
    "promo_session_expired": "セッションが切れました。先にトラックを検索してください。",
    "top_empty": "まだランキングに貢献者がいません。",
    "top_title": "🏆 <b>TrackCredits 貢献者ランキング</b> — {page}ページ",
    "top_prev": "前へ",
    "top_next": "次へ",
    "top_footer": "承認されたクレジット/歌詞 = +5pt · バグ報告 = +2pt",
    "metrics_empty": "<i>まだメトリクスデータがありません。</i>",
    "admin_dashboard": "<b>管理者ダッシュボード</b>\n保留中：{count}\n\n先にトラックを検索し、/adminでプロモリンクを追加してください。",
    "admin_promo_title": "プロモ設定：",
    "admin_btn_drums": "Drums + Bass リンクを追加",
    "admin_btn_instrumental": "Instrumental リンクを追加",
    "admin_btn_custom_promo": "➕ カスタムタイプ…",
    "admin_btn_clear_promo": "すべてのプロモリンクを削除",
    "admin_promo_prompt": "ADMIN：'{promo_type}'バージョンのYouTubeリンクを送ってください（または/cancel）。",
    "admin_promo_name_prompt": "ADMIN：カスタムプロモタイプ名を入力してください（例：カラオケ）、その後YouTubeリンクを送ってください。",
    "admin_promo_cleared": "このトラックのすべてのプロモリンクを削除しました。",
    "admin_invalid_request": "無効な管理者リクエストです。",
    "admin_sub_not_found": "投稿が見つかりません。",
    "admin_already_processed": "この投稿はすでに処理されています。",
    "admin_approved": "{title}の{sub_type}を承認しました",
    "admin_rejected": "{title}の{sub_type}を拒否しました",
    "user_contrib_approved": "<b>{title}</b>への{sub_type}の投稿が承認されました。",
    "disambig_prompt": "🔎 <b>'{query}'というアーティストが複数います。正しい方を選んでください：</b>",
    "disambig_none": "どれでもない",
    "invalid_page": "無効なページです。",
    "search_prompt": "トラックのリンクまたはタイトルを送ってください：",
    "invalid_choice": "無効な選択です。",
    "choice_expired": "この選択はもう有効ではありません。",
    "searching_other_artists": "'{title}'の他のアーティストを検索中...",
    "no_other_artists": "<b>{title}</b>の他のアーティストは見つかりませんでした。\n\nSpotify/YouTubeのリンクを直接送ってみてください。",
    "lyrics_source_label": "出典：{source}",
    "community_desc_header": "\n\n📝 <b>コミュニティの説明：</b>\n\n",
    "community_source_label": "\n出典：{source}",
    "community_contrib_label": "\n投稿者：@{contributor}",
    "credits_community_by": "\n\n<i>コミュニティクレジット by：@{contributor}</i>",
    "view_on_genius": "Geniusで見る",
    "listen_on_spotify": "Spotifyで聴く",
    "credits_section_title": "<b>オリジナル曲クレジット：</b>",
    "credits_no_data": "<i>オリジナルクレジットはありません。</i>",
    "credits_community_section": "\n📝 <b>コミュニティの説明：</b>",
    "credits_rights": "\nすべての元の権利は{artist}および各クリエイターに帰属します。",
    "btn_lrc": "⏱ 同期 (.lrc)",
    "lrc_title": "同期歌詞 (.lrc)",
},
"zh": {
    "start_prompt": "请选择您的语言：",
    "welcome": "欢迎使用 TrackCredits。\n\n发送歌曲链接或输入歌曲名称，即可获取版权信息、歌词和流媒体链接。",
    "help_txt": "<b>使用方法</b>\n\n发送歌曲标题或 Spotify/YouTube/Apple Music 链接。\n使用 /cancel 取消当前操作。\n使用 /top 查看贡献者排行榜。\n使用 /lang 切换语言。\n内联模式：<code>@bot 歌曲名</code>",
    "analyzing": "正在分析歌曲数据...",
    "not_found": "未找到歌曲。",
    "rate_limited": "您发送请求太快，请稍候几秒。",
    "session_expired": "会话已过期，请重新发送歌曲。",
    "loaded": "数据已加载，请选择选项。",
    "cache_hit": "从缓存加载。请选择选项。",
    "streams_title": "<b>流媒体平台：</b>",
    "search_links": "<b>备用搜索链接：</b>",
    "lyrics_title": "🎤 歌词",
    "no_lyrics": "<i>暂无歌词。</i>",
    "contrib_prompt": "您想贡献什么？",
    "req_credits": "发送版权信息或歌曲备注：",
    "req_lyrics1": "第1步/共2步：发送歌词：",
    "req_lyrics2": "第2步/共2步：发送来源 / 原作者：",
    "req_report": "描述您发现的问题：",
    "submitted": "已提交，管理员将很快审核。",
    "lyrics_already_exists": "此歌曲已有来自 <b>{source}</b> 的歌词。\n如需更正，请使用<b>举报</b>按钮。",
    "btn_view_song": "查看歌曲",
    "btn_streams": "流媒体",
    "btn_credits": "版权信息",
    "btn_lyrics": "歌词",
    "btn_contrib": "贡献",
    "btn_report": "举报",
    "btn_wrong": "歌曲不对",
    "btn_back": "返回",
    "cancel_with_track": "当前操作已取消。",
    "cancel_no_track": "已取消。发送歌曲标题或链接进行搜索。",
    "btn_continue_track": "继续当前歌曲",
    "btn_new_search": "搜索新歌曲",
    "wrong_result": "如果结果不对，请用<b>歌曲名 + 艺术家</b>重试，或发送直接链接。",
    "access_denied": "访问被拒绝。",
    "input_too_long": "查询太长，请缩短。",
    "url_extract_failed": "无法从此链接提取数据，请尝试歌曲名称或其他链接。",
    "track_load_failed": "无法加载歌曲数据。",
    "content_too_long": "内容太长，请缩短后重新提交。",
    "promo_session_expired": "会话已过期，请先搜索歌曲。",
    "top_empty": "排行榜上暂无贡献者。",
    "top_title": "🏆 <b>TrackCredits 贡献者排行榜</b> — 第{page}页",
    "top_prev": "上一页",
    "top_next": "下一页",
    "top_footer": "已批准的版权/歌词 = +5分 · 错误举报 = +2分",
    "metrics_empty": "<i>暂无统计数据。</i>",
    "admin_dashboard": "<b>管理员控制台</b>\n待处理：{count}\n\n请先找到歌曲，然后使用 /admin 添加推广链接。",
    "admin_promo_title": "推广设置：",
    "admin_btn_drums": "添加 Drums + Bass 链接",
    "admin_btn_instrumental": "添加 Instrumental 链接",
    "admin_btn_custom_promo": "➕ 自定义类型…",
    "admin_btn_clear_promo": "清除所有推广链接",
    "admin_promo_prompt": "管理员：请发送'{promo_type}'版本的 YouTube 链接（或 /cancel）。",
    "admin_promo_name_prompt": "管理员：输入自定义推广类型名称（例如：卡拉OK），然后发送 YouTube 链接。",
    "admin_promo_cleared": "此歌曲的所有推广链接已清除。",
    "admin_invalid_request": "无效的管理员请求。",
    "admin_sub_not_found": "未找到提交内容。",
    "admin_already_processed": "此提交已处理。",
    "admin_approved": "已批准 {title} 的 {sub_type}",
    "admin_rejected": "已拒绝 {title} 的 {sub_type}",
    "user_contrib_approved": "您对 <b>{title}</b> 的 {sub_type} 贡献已获批准。",
    "disambig_prompt": "🔎 <b>有多位名为 '{query}' 的艺术家，请选择正确的：</b>",
    "disambig_none": "都不是",
    "invalid_page": "无效的页面。",
    "search_prompt": "发送歌曲链接或标题：",
    "invalid_choice": "无效的选择。",
    "choice_expired": "此选择已失效。",
    "searching_other_artists": "正在搜索其他有 '{title}' 的艺术家...",
    "no_other_artists": "未找到 <b>{title}</b> 的其他艺术家。\n\n请尝试直接发送 Spotify/YouTube 链接。",
    "lyrics_source_label": "来源：{source}",
    "community_desc_header": "\n\n📝 <b>社区描述：</b>\n\n",
    "community_source_label": "\n来源：{source}",
    "community_contrib_label": "\n贡献者：@{contributor}",
    "credits_community_by": "\n\n<i>社区版权信息由：@{contributor}</i>",
    "view_on_genius": "在 Genius 上查看",
    "listen_on_spotify": "在 Spotify 上收听",
    "credits_section_title": "<b>原曲版权信息：</b>",
    "credits_no_data": "<i>暂无原曲版权信息。</i>",
    "credits_community_section": "\n📝 <b>社区描述：</b>",
    "credits_rights": "\n所有原版权利属于 {artist} 及各创作者。",
    "btn_lrc": "⏱ 同步歌词 (.lrc)",
    "lrc_title": "同步歌词 (.lrc)",
},
"ar": {
    "start_prompt": "الرجاء اختيار لغتك:",
    "welcome": "مرحباً بك في TrackCredits.\n\nأرسل رابط أغنية أو اكتب اسمها للحصول على الائتمانات والكلمات وروابط البث.",
    "help_txt": "<b>كيفية الاستخدام</b>\n\nأرسل عنوان أغنية أو رابط Spotify/YouTube/Apple Music.\nاستخدم /cancel لإلغاء الإجراء الحالي.\nاستخدم /top لرؤية لوحة المتصدرين.\nاستخدم /lang لتغيير اللغة.\nالوضع المضمّن: <code>@bot اسم_الأغنية</code>",
    "analyzing": "جارٍ تحليل بيانات المقطع...",
    "not_found": "لم يتم العثور على المقطع.",
    "rate_limited": "أنت ترسل الطلبات بسرعة كبيرة. الرجاء الانتظار بضع ثوانٍ.",
    "session_expired": "انتهت صلاحية الجلسة. الرجاء إرسال المقطع مجدداً.",
    "loaded": "تم تحميل البيانات. اختر خياراً.",
    "cache_hit": "تم التحميل من الذاكرة المؤقتة. اختر خياراً.",
    "streams_title": "<b>منصات البث:</b>",
    "search_links": "<b>روابط البحث الاحتياطية:</b>",
    "lyrics_title": "🎤 الكلمات",
    "no_lyrics": "<i>الكلمات غير متاحة بعد.</i>",
    "contrib_prompt": "ماذا تريد أن تساهم؟",
    "req_credits": "أرسل الائتمانات أو ملاحظات المقطع:",
    "req_lyrics1": "الخطوة 1/2: أرسل الكلمات:",
    "req_lyrics2": "الخطوة 2/2: أرسل المصدر / المؤلف الأصلي:",
    "req_report": "صف المشكلة التي وجدتها:",
    "submitted": "تم الإرسال. سيراجعه المسؤول قريباً.",
    "lyrics_already_exists": "هذا المقطع لديه بالفعل كلمات من <b>{source}</b>.\nإذا أردت تصحيحها، استخدم زر <b>الإبلاغ</b>.",
    "btn_view_song": "عرض الأغنية",
    "btn_streams": "البث",
    "btn_credits": "الائتمانات",
    "btn_lyrics": "الكلمات",
    "btn_contrib": "المساهمة",
    "btn_report": "الإبلاغ",
    "btn_wrong": "مقطع خاطئ",
    "btn_back": "رجوع",
    "cancel_with_track": "تم إلغاء الإجراء الحالي.",
    "cancel_no_track": "تم الإلغاء. أرسل عنوان أغنية أو رابطاً للبحث.",
    "btn_continue_track": "متابعة المقطع الحالي",
    "btn_new_search": "البحث عن مقطع جديد",
    "wrong_result": "إذا كانت النتيجة خاطئة، حاول مجدداً بـ<b>اسم الأغنية + الفنان</b> أو أرسل رابطاً مباشراً.",
    "access_denied": "تم رفض الوصول.",
    "input_too_long": "الاستعلام طويل جداً. الرجاء تقصيره.",
    "url_extract_failed": "تعذّر استخراج البيانات من هذا الرابط. جرّب عنوان أغنية أو رابطاً مختلفاً.",
    "track_load_failed": "تعذّر تحميل بيانات المقطع.",
    "content_too_long": "المحتوى طويل جداً. الرجاء تقصيره وإعادة الإرسال.",
    "promo_session_expired": "انتهت صلاحية الجلسة. ابحث عن مقطع أولاً.",
    "top_empty": "لا يوجد مساهمون في لوحة المتصدرين بعد.",
    "top_title": "🏆 <b>لوحة متصدري TrackCredits</b> — الصفحة {page}",
    "top_prev": "السابق",
    "top_next": "التالي",
    "top_footer": "ائتمانات/كلمات معتمدة = +5 نقاط · تقرير خطأ = +2 نقاط",
    "metrics_empty": "<i>لا توجد بيانات مقاييس بعد.</i>",
    "admin_dashboard": "<b>لوحة تحكم المسؤول</b>\nقيد الانتظار: {count}\n\nابحث عن مقطع أولاً، ثم استخدم /admin لإضافة روابط ترويجية.",
    "admin_promo_title": "إعدادات الترويج لـ:",
    "admin_btn_drums": "إضافة رابط Drums + Bass",
    "admin_btn_instrumental": "إضافة رابط Instrumental",
    "admin_btn_custom_promo": "➕ نوع مخصص…",
    "admin_btn_clear_promo": "مسح جميع الروابط الترويجية",
    "admin_promo_prompt": "المسؤول: أرسل رابط YouTube لنسخة '{promo_type}' (أو /cancel).",
    "admin_promo_name_prompt": "المسؤول: اكتب اسم نوع الترويج المخصص (مثل: كاريوكي)، ثم أرسل رابط YouTube.",
    "admin_promo_cleared": "تم مسح جميع الروابط الترويجية لهذا المقطع.",
    "admin_invalid_request": "طلب مسؤول غير صالح.",
    "admin_sub_not_found": "لم يتم العثور على الإرسال.",
    "admin_already_processed": "تمت معالجة هذا الإرسال بالفعل.",
    "admin_approved": "تمت الموافقة على {sub_type} لـ: {title}",
    "admin_rejected": "تم رفض {sub_type} لـ: {title}",
    "user_contrib_approved": "تمت الموافقة على مساهمتك {sub_type} لـ <b>{title}</b>.",
    "disambig_prompt": "🔎 <b>يوجد عدة فنانين باسم '{query}'. اختر الصحيح:</b>",
    "disambig_none": "لا أحد من هؤلاء",
    "invalid_page": "صفحة غير صالحة.",
    "search_prompt": "أرسل رابط أو عنوان مقطع:",
    "invalid_choice": "اختيار غير صالح.",
    "choice_expired": "هذا الاختيار لم يعد صالحاً.",
    "searching_other_artists": "جارٍ البحث عن فنانين آخرين بـ'{title}'...",
    "no_other_artists": "لم يتم العثور على فنانين آخرين لـ<b>{title}</b>.\n\nجرّب إرسال رابط Spotify/YouTube مباشرة.",
    "lyrics_source_label": "المصدر: {source}",
    "community_desc_header": "\n\n📝 <b>وصف المجتمع:</b>\n\n",
    "community_source_label": "\nالمصدر: {source}",
    "community_contrib_label": "\nساهم به: @{contributor}",
    "credits_community_by": "\n\n<i>ائتمانات المجتمع بواسطة: @{contributor}</i>",
    "view_on_genius": "عرض على Genius",
    "listen_on_spotify": "استماع على Spotify",
    "credits_section_title": "<b>ائتمانات الأغنية الأصلية:</b>",
    "credits_no_data": "<i>لا توجد ائتمانات أصلية.</i>",
    "credits_community_section": "\n📝 <b>وصف المجتمع:</b>",
    "credits_rights": "\nجميع الحقوق الأصلية تعود إلى {artist} والمبدعين المعنيين.",
    "btn_lrc": "⏱ مزامن (.lrc)",
    "lrc_title": "كلمات مزامنة (.lrc)",
},
}

LANG_DICT.update(_EXTRA_LANGS)


# ── Patch: inject buy/terms/privacy keys for all non-EN languages ─────────
# These keys were added after the initial release and are patched in here
# to keep the main LANG_DICT blocks clean and auditable.
# IMPORTANT: use per-key merge, not dict replace.
_EXTRA_LANGS: dict[str, dict] = {
    "vi": {
        "terms_text": (
            "<b>📋 Điều khoản sử dụng</b>\n\n"
            "Khi dùng TrackCredits Bot bạn đồng ý:\n"
            "• Chỉ sử dụng cho mục đích cá nhân, phi thương mại.\n"
            "• Không lạm dụng giới hạn yêu cầu hoặc thu thập dữ liệu hàng loạt.\n"
            "• Không gửi nội dung sai lệch, gây hiểu nhầm hoặc vi phạm bản quyền.\n"
            "• Chấp nhận rằng credits không được hoàn lại sau khi mua.\n\n"
            "Bot được cung cấp nguyên trạng, không có bảo hành. "
            "Dịch vụ có thể bị đình chỉ khi vi phạm điều khoản.\n\n"
            "<i>Cập nhật lần cuối: 2025-01-01</i>"
        ),
        "privacy_text": (
            "<b>🔒 Chính sách quyền riêng tư</b>\n\n"
            "<b>Dữ liệu chúng tôi thu thập</b>\n"
            "• ID Telegram và tên người dùng (cho credits và bảng xếp hạng).\n"
            "• Lịch sử tìm kiếm và đóng góp (cho cache và thống kê).\n"
            "• Giao dịch credits (cho thanh toán và giải quyết tranh chấp).\n\n"
            "<b>Dữ liệu chúng tôi KHÔNG thu thập</b>\n"
            "• Tên thật, email, số điện thoại hoặc thông tin thẻ ngân hàng.\n"
            "• Nội dung tin nhắn ngoài tương tác với bot.\n\n"
            "<b>Lưu giữ dữ liệu</b>\n"
            "Cache tìm kiếm: 14 ngày. Dữ liệu người dùng: lưu trong thời gian sử dụng. "
            "Yêu cầu xóa bất kỳ lúc nào qua /cancel và liên hệ admin.\n\n"
            "<b>Dịch vụ bên thứ ba</b>\n"
            "Lời bài hát từ Genius, lrclib.net, lyrics.ovh. "
            "Credits từ MusicBrainz và YouTube. "
            "Link nghe nhạc qua Odesli.\n\n"
            "<i>Cập nhật lần cuối: 2025-01-01</i>"
        ),
        "user_contrib_rejected": (
            "Đóng góp {sub_type} của bạn cho <b>{title}</b> chưa được duyệt lần này.\n"
            "Hãy thử lại với thông tin mới nhé!"
        ),
        "buy_title": "💎 <b>Mua Credits</b>",
        "buy_balance": "Số dư hiện tại: <b>{balance} credits</b>",
        "buy_provider_momo": "💳 Thanh toán qua MoMo",
        "buy_provider_stripe": "💳 Thanh toán qua Stripe (thẻ quốc tế)",
        "buy_provider_manual": "🏦 Chuyển khoản thủ công — admin xác nhận sau khi nhận tiền",
        "buy_success": "🎉 <b>+{credits} credits</b> đã được nạp!\nSố dư mới: <b>{balance}</b>.",
        "buy_error": "⚠️ Lỗi thanh toán. Vui lòng thử lại hoặc liên hệ admin.",
    },
    "es": {
        "terms_text": (
            "<b>📋 Términos de uso</b>\n\n"
            "Al usar TrackCredits Bot aceptas:\n"
            "• Usar el bot únicamente para uso personal y no comercial.\n"
            "• No abusar de los límites de velocidad ni intentar extraer datos masivamente.\n"
            "• No enviar contenido falso, engañoso o con derechos de autor como contribuciones.\n"
            "• Aceptar que los créditos no son reembolsables una vez comprados.\n\n"
            "El bot se proporciona tal cual, sin garantías. "
            "El servicio puede suspenderse por violación de estos términos.\n\n"
            "<i>Última actualización: 2025-01-01</i>"
        ),
        "privacy_text": (
            "<b>🔒 Política de privacidad</b>\n\n"
            "<b>Qué recopilamos</b>\n"
            "• Tu ID de Telegram y nombre de usuario (para créditos y ranking).\n"
            "• Historial de búsquedas y contribuciones (para caché y análisis).\n"
            "• Transacciones de créditos (para facturación y resolución de disputas).\n\n"
            "<b>Qué NO recopilamos</b>\n"
            "• Tu nombre real, correo electrónico, teléfono o datos de tarjeta de crédito.\n"
            "• Contenido de mensajes fuera de las interacciones con el bot.\n\n"
            "<b>Retención de datos</b>\n"
            "Caché de búsqueda: 14 días. Datos de usuario: retenidos mientras uses el bot. "
            "Solicita eliminación en cualquier momento contactando al admin.\n\n"
            "<b>Servicios de terceros</b>\n"
            "Letras de Genius, lrclib.net, lyrics.ovh. "
            "Créditos de MusicBrainz y YouTube. "
            "Links de plataformas vía Odesli.\n\n"
            "<i>Última actualización: 2025-01-01</i>"
        ),
        "user_contrib_rejected": (
            "Tu contribución {sub_type} para <b>{title}</b> no fue aprobada esta vez.\n"
            "¡No dudes en intentarlo de nuevo con información actualizada!"
        ),
        "buy_title": "💎 <b>Comprar créditos</b>",
        "buy_balance": "Saldo actual: <b>{balance} créditos</b>",
        "buy_provider_momo": "💳 Pago vía MoMo",
        "buy_provider_stripe": "💳 Pago vía Stripe (tarjeta)",
        "buy_provider_manual": "🏦 Transferencia manual — el admin confirma después del pago",
        "buy_success": "🎉 <b>+{credits} créditos</b> añadidos.\nNuevo saldo: <b>{balance}</b>.",
        "buy_error": "⚠️ Error de pago. Por favor intenta de nuevo o contacta al admin.",
    },
    "pt": {
        "terms_text": (
            "<b>📋 Termos de uso</b>\n\n"
            "Ao usar o TrackCredits Bot você concorda em:\n"
            "• Usar o bot apenas para fins pessoais e não comerciais.\n"
            "• Não abusar dos limites de taxa nem tentar raspar dados em escala.\n"
            "• Não enviar conteúdo falso, enganoso ou protegido por direitos autorais como contribuições.\n"
            "• Aceitar que os créditos não são reembolsáveis após a compra.\n\n"
            "O bot é fornecido como está, sem garantias. "
            "O serviço pode ser suspenso por violação destes termos.\n\n"
            "<i>Última atualização: 2025-01-01</i>"
        ),
        "privacy_text": (
            "<b>🔒 Política de privacidade</b>\n\n"
            "<b>O que coletamos</b>\n"
            "• Seu ID do Telegram e nome de usuário (para créditos e ranking).\n"
            "• Histórico de buscas e contribuições (para cache e análise).\n"
            "• Transações de créditos (para cobrança e resolução de disputas).\n\n"
            "<b>O que NÃO coletamos</b>\n"
            "• Seu nome real, e-mail, telefone ou dados de cartão de crédito.\n"
            "• Conteúdo de mensagens fora das interações com o bot.\n\n"
            "<b>Retenção de dados</b>\n"
            "Cache de busca: 14 dias. Dados do usuário: retidos enquanto usar o bot. "
            "Solicite exclusão a qualquer momento entrando em contato com o admin.\n\n"
            "<b>Serviços de terceiros</b>\n"
            "Letras do Genius, lrclib.net, lyrics.ovh. "
            "Créditos do MusicBrainz e YouTube. "
            "Links de plataformas via Odesli.\n\n"
            "<i>Última atualização: 2025-01-01</i>"
        ),
        "user_contrib_rejected": (
            "Sua contribuição {sub_type} para <b>{title}</b> não foi aprovada desta vez.\n"
            "Sinta-se à vontade para tentar novamente com informações atualizadas!"
        ),
        "buy_title": "💎 <b>Comprar créditos</b>",
        "buy_balance": "Saldo atual: <b>{balance} créditos</b>",
        "buy_provider_momo": "💳 Pagamento via MoMo",
        "buy_provider_stripe": "💳 Pagamento via Stripe (cartão)",
        "buy_provider_manual": "🏦 Transferência manual — o admin confirma após o pagamento",
        "buy_success": "🎉 <b>+{credits} créditos</b> adicionados!\nNovo saldo: <b>{balance}</b>.",
        "buy_error": "⚠️ Erro no pagamento. Por favor tente novamente ou contate o admin.",
    },
    "fr": {
        "terms_text": (
            "<b>📋 Conditions d'utilisation</b>\n\n"
            "En utilisant TrackCredits Bot, vous acceptez de :\n"
            "• Utiliser le bot uniquement à des fins personnelles et non commerciales.\n"
            "• Ne pas abuser des limites de débit ni tenter d'extraire des données en masse.\n"
            "• Ne pas soumettre de contenu faux, trompeur ou protégé par des droits d'auteur.\n"
            "• Accepter que les crédits ne sont pas remboursables une fois achetés.\n\n"
            "Le bot est fourni tel quel, sans garantie. "
            "Le service peut être suspendu en cas de violation de ces conditions.\n\n"
            "<i>Dernière mise à jour : 2025-01-01</i>"
        ),
        "privacy_text": (
            "<b>🔒 Politique de confidentialité</b>\n\n"
            "<b>Ce que nous collectons</b>\n"
            "• Votre ID Telegram et nom d'utilisateur (pour les crédits et le classement).\n"
            "• Historique des recherches et contributions (pour le cache et les analyses).\n"
            "• Transactions de crédits (pour la facturation et la résolution des litiges).\n\n"
            "<b>Ce que nous NE collectons PAS</b>\n"
            "• Votre nom réel, e-mail, téléphone ou données de carte bancaire.\n"
            "• Le contenu des messages en dehors des interactions avec le bot.\n\n"
            "<b>Conservation des données</b>\n"
            "Cache de recherche : 14 jours. Données utilisateur : conservées pendant l'utilisation. "
            "Demandez la suppression à tout moment en contactant l'admin.\n\n"
            "<b>Services tiers</b>\n"
            "Paroles via Genius, lrclib.net, lyrics.ovh. "
            "Crédits via MusicBrainz et YouTube. "
            "Liens de plateformes via Odesli.\n\n"
            "<i>Dernière mise à jour : 2025-01-01</i>"
        ),
        "user_contrib_rejected": (
            "Votre contribution {sub_type} pour <b>{title}</b> n'a pas été approuvée cette fois.\n"
            "N'hésitez pas à réessayer avec des informations mises à jour !"
        ),
        "buy_title": "💎 <b>Acheter des crédits</b>",
        "buy_balance": "Solde actuel : <b>{balance} crédits</b>",
        "buy_provider_momo": "💳 Paiement via MoMo",
        "buy_provider_stripe": "💳 Paiement via Stripe (carte)",
        "buy_provider_manual": "🏦 Virement manuel — l'admin confirme après réception",
        "buy_success": "🎉 <b>+{credits} crédits</b> ajoutés !\nNouveau solde : <b>{balance}</b>.",
        "buy_error": "⚠️ Erreur de paiement. Veuillez réessayer ou contacter l'admin.",
    },
    "ru": {
        "terms_text": (
            "<b>📋 Условия использования</b>\n\n"
            "Используя TrackCredits Bot, вы соглашаетесь:\n"
            "• Использовать бот только в личных, некоммерческих целях.\n"
            "• Не злоупотреблять ограничениями скорости и не собирать данные в промышленных масштабах.\n"
            "• Не отправлять ложные, вводящие в заблуждение или защищённые авторским правом материалы.\n"
            "• Принять, что кредиты не возвращаются после покупки.\n\n"
            "Бот предоставляется как есть, без гарантий. "
            "Сервис может быть приостановлен при нарушении условий.\n\n"
            "<i>Последнее обновление: 2025-01-01</i>"
        ),
        "privacy_text": (
            "<b>🔒 Политика конфиденциальности</b>\n\n"
            "<b>Что мы собираем</b>\n"
            "• Ваш ID Telegram и имя пользователя (для кредитов и рейтинга).\n"
            "• Историю поиска и вклада (для кэша и аналитики).\n"
            "• Транзакции кредитов (для биллинга и разрешения споров).\n\n"
            "<b>Что мы НЕ собираем</b>\n"
            "• Ваше имя, e-mail, телефон или данные банковской карты.\n"
            "• Содержимое сообщений вне взаимодействия с ботом.\n\n"
            "<b>Хранение данных</b>\n"
            "Кэш поиска: 14 дней. Данные пользователя: хранятся пока вы используете бот. "
            "Запросить удаление можно в любое время, связавшись с админом.\n\n"
            "<b>Сторонние сервисы</b>\n"
            "Тексты песен от Genius, lrclib.net, lyrics.ovh. "
            "Кредиты от MusicBrainz и YouTube. "
            "Ссылки на платформы через Odesli.\n\n"
            "<i>Последнее обновление: 2025-01-01</i>"
        ),
        "user_contrib_rejected": (
            "Ваш вклад {sub_type} для <b>{title}</b> не был одобрен на этот раз.\n"
            "Попробуйте снова с обновлёнными данными!"
        ),
        "buy_title": "💎 <b>Купить кредиты</b>",
        "buy_balance": "Текущий баланс: <b>{balance} кредитов</b>",
        "buy_provider_momo": "💳 Оплата через MoMo",
        "buy_provider_stripe": "💳 Оплата через Stripe (карта)",
        "buy_provider_manual": "🏦 Ручной перевод — админ подтверждает после получения",
        "buy_success": "🎉 <b>+{credits} кредитов</b> добавлено!\nНовый баланс: <b>{balance}</b>.",
        "buy_error": "⚠️ Ошибка оплаты. Попробуйте снова или свяжитесь с админом.",
    },
    "ko": {
        "terms_text": (
            "<b>📋 이용 약관</b>\n\n"
            "TrackCredits Bot을 사용함으로써 다음에 동의합니다:\n"
            "• 개인적이고 비상업적인 목적으로만 봇을 사용합니다.\n"
            "• 요청 제한을 남용하거나 대규모 데이터 수집을 시도하지 않습니다.\n"
            "• 허위, 오해의 소지가 있거나 저작권이 있는 콘텐츠를 기여로 제출하지 않습니다.\n"
            "• 구매한 크레딧은 환불되지 않음을 수락합니다.\n\n"
            "봇은 보증 없이 현재 상태로 제공됩니다. "
            "약관 위반 시 서비스가 중단될 수 있습니다.\n\n"
            "<i>최종 업데이트: 2025-01-01</i>"
        ),
        "privacy_text": (
            "<b>🔒 개인정보 보호정책</b>\n\n"
            "<b>수집하는 정보</b>\n"
            "• Telegram 사용자 ID와 사용자명 (크레딧 및 리더보드용).\n"
            "• 검색 및 기여 내역 (캐시 및 분석용).\n"
            "• 크레딧 거래 내역 (결제 및 분쟁 해결용).\n\n"
            "<b>수집하지 않는 정보</b>\n"
            "• 실명, 이메일, 전화번호 또는 카드 정보.\n"
            "• 봇 상호작용 외의 메시지 내용.\n\n"
            "<b>데이터 보존</b>\n"
            "검색 캐시: 14일. 사용자 데이터: 봇 사용 중 보관. "
            "언제든지 관리자에게 연락하여 삭제를 요청할 수 있습니다.\n\n"
            "<b>제3자 서비스</b>\n"
            "Genius, lrclib.net, lyrics.ovh에서 가사 제공. "
            "MusicBrainz 및 YouTube에서 크레딧 제공. "
            "Odesli를 통한 플랫폼 링크.\n\n"
            "<i>최종 업데이트: 2025-01-01</i>"
        ),
        "user_contrib_rejected": (
            "<b>{title}</b>에 대한 {sub_type} 기여가 이번에는 승인되지 않았습니다.\n"
            "업데이트된 정보로 다시 시도해 주세요!"
        ),
        "buy_title": "💎 <b>크레딧 구매</b>",
        "buy_balance": "현재 잔액: <b>{balance} 크레딧</b>",
        "buy_provider_momo": "💳 MoMo로 결제",
        "buy_provider_stripe": "💳 Stripe로 결제 (카드)",
        "buy_provider_manual": "🏦 수동 이체 — 결제 후 관리자 확인",
        "buy_success": "🎉 <b>+{credits} 크레딧</b>이 추가되었습니다!\n새 잔액: <b>{balance}</b>.",
        "buy_error": "⚠️ 결제 오류. 다시 시도하거나 관리자에게 문의하세요.",
    },
    "ja": {
        "terms_text": (
            "<b>📋 利用規約</b>\n\n"
            "TrackCredits Botを使用することで、以下に同意したものとみなされます:\n"
            "• 個人的かつ非商業的な目的でのみボットを使用する。\n"
            "• レート制限を悪用したり、大規模なデータ収集を試みない。\n"
            "• 虚偽、誤解を招く、または著作権で保護されたコンテンツを提出しない。\n"
            "• 購入後のクレジットは返金不可であることを承諾する。\n\n"
            "ボットは保証なしに現状のまま提供されます。 "
            "規約違反の場合、サービスが停止される場合があります。\n\n"
            "<i>最終更新: 2025-01-01</i>"
        ),
        "privacy_text": (
            "<b>🔒 プライバシーポリシー</b>\n\n"
            "<b>収集する情報</b>\n"
            "• TelegramユーザーIDとユーザー名 (クレジットとリーダーボード用)。\n"
            "• 検索と貢献の履歴 (キャッシュと分析用)。\n"
            "• クレジット取引 (請求と紛争解決用)。\n\n"
            "<b>収集しない情報</b>\n"
            "• 本名、メール、電話番号、またはカード情報。\n"
            "• ボットとのやり取り以外のメッセージ内容。\n\n"
            "<b>データの保持</b>\n"
            "検索キャッシュ: 14日間。ユーザーデータ: ボット使用中保持。 "
            "いつでも管理者に連絡して削除をリクエストできます。\n\n"
            "<b>サードパーティサービス</b>\n"
            "Genius、lrclib.net、lyrics.ovhから歌詞を提供。 "
            "MusicBrainzとYouTubeからクレジット提供。 "
            "Odesliを通じたプラットフォームリンク。\n\n"
            "<i>最終更新: 2025-01-01</i>"
        ),
        "user_contrib_rejected": (
            "<b>{title}</b>への{sub_type}の投稿は今回は承認されませんでした。\n"
            "更新された情報で再度お試しください！"
        ),
        "buy_title": "💎 <b>クレジットを購入</b>",
        "buy_balance": "現在の残高: <b>{balance} クレジット</b>",
        "buy_provider_momo": "💳 MoMoで支払い",
        "buy_provider_stripe": "💳 Stripeで支払い (カード)",
        "buy_provider_manual": "🏦 手動振込 — 支払い後に管理者が確認",
        "buy_success": "🎉 <b>+{credits} クレジット</b>が追加されました！\n新しい残高: <b>{balance}</b>。",
        "buy_error": "⚠️ 支払いエラー。再試行するか管理者にお問い合わせください。",
    },
    "zh": {
        "terms_text": (
            "<b>📋 使用条款</b>\n\n"
            "使用 TrackCredits Bot 即表示您同意：\n"
            "• 仅将机器人用于个人、非商业目的。\n"
            "• 不滥用速率限制，也不尝试大规模抓取数据。\n"
            "• 不提交虚假、误导性或受版权保护的内容作为贡献。\n"
            "• 接受购买后的积分不可退款。\n\n"
            "机器人按原样提供，不附带任何保证。 "
            "违反条款可能导致服务被暂停。\n\n"
            "<i>最后更新：2025-01-01</i>"
        ),
        "privacy_text": (
            "<b>🔒 隐私政策</b>\n\n"
            "<b>我们收集的内容</b>\n"
            "• 您的 Telegram 用户 ID 和用户名（用于积分和排行榜）。\n"
            "• 搜索和贡献历史记录（用于缓存和分析）。\n"
            "• 积分交易（用于计费和纠纷解决）。\n\n"
            "<b>我们不收集的内容</b>\n"
            "• 您的真实姓名、电子邮件、电话号码或银行卡信息。\n"
            "• 机器人交互以外的消息内容。\n\n"
            "<b>数据保留</b>\n"
            "搜索缓存：14 天。用户数据：在使用机器人期间保留。 "
            "随时联系管理员请求删除。\n\n"
            "<b>第三方服务</b>\n"
            "来自 Genius、lrclib.net、lyrics.ovh 的歌词。 "
            "来自 MusicBrainz 和 YouTube 的制作信息。 "
            "通过 Odesli 提供平台链接。\n\n"
            "<i>最后更新：2025-01-01</i>"
        ),
        "user_contrib_rejected": (
            "您对 <b>{title}</b> 的 {sub_type} 贡献这次未获批准。\n"
            "欢迎用更新的信息再次尝试！"
        ),
        "buy_title": "💎 <b>购买积分</b>",
        "buy_balance": "当前余额：<b>{balance} 积分</b>",
        "buy_provider_momo": "💳 通过 MoMo 支付",
        "buy_provider_stripe": "💳 通过 Stripe 支付（银行卡）",
        "buy_provider_manual": "🏦 手动转账 — 付款后由管理员确认",
        "buy_success": "🎉 已添加 <b>+{credits} 积分</b>！\n新余额：<b>{balance}</b>。",
        "buy_error": "⚠️ 支付错误。请重试或联系管理员。",
    },
    "ar": {
        "terms_text": (
            "<b>📋 شروط الاستخدام</b>\n\n"
            "باستخدام TrackCredits Bot توافق على:\n"
            "• استخدام البوت للأغراض الشخصية وغير التجارية فقط.\n"
            "• عدم إساءة استخدام حدود معدل الطلبات أو محاولة جمع البيانات على نطاق واسع.\n"
            "• عدم تقديم محتوى زائف أو مضلل أو محمي بحقوق الملكية.\n"
            "• قبول أن الرصيد غير قابل للاسترداد بعد الشراء.\n\n"
            "يُقدَّم البوت كما هو دون أي ضمانات. "
            "قد يُوقَف الخدمة عند انتهاك هذه الشروط.\n\n"
            "<i>آخر تحديث: 2025-01-01</i>"
        ),
        "privacy_text": (
            "<b>🔒 سياسة الخصوصية</b>\n\n"
            "<b>ما نجمعه</b>\n"
            "• معرّف Telegram واسم المستخدم (للرصيد والمتصدرين).\n"
            "• سجل البحث والمساهمات (للتخزين المؤقت والتحليلات).\n"
            "• معاملات الرصيد (للفوترة وحل النزاعات).\n\n"
            "<b>ما لا نجمعه</b>\n"
            "• اسمك الحقيقي أو البريد الإلكتروني أو الهاتف أو بيانات البطاقة.\n"
            "• محتوى الرسائل خارج التفاعلات مع البوت.\n\n"
            "<b>الاحتفاظ بالبيانات</b>\n"
            "ذاكرة التخزين المؤقت للبحث: 14 يوم. بيانات المستخدم: محتفظ بها طوال فترة الاستخدام. "
            "اطلب الحذف في أي وقت بالتواصل مع المشرف.\n\n"
            "<b>خدمات الطرف الثالث</b>\n"
            "كلمات الأغاني من Genius وlrclib.net وlyrics.ovh. "
            "الاعتمادات من MusicBrainz وYouTube. "
            "روابط المنصات عبر Odesli.\n\n"
            "<i>آخر تحديث: 2025-01-01</i>"
        ),
        "user_contrib_rejected": (
            "مساهمتك {sub_type} لـ <b>{title}</b> لم تتم الموافقة عليها هذه المرة.\n"
            "لا تتردد في المحاولة مرة أخرى بمعلومات محدّثة!"
        ),
        "buy_title": "💎 <b>شراء رصيد</b>",
        "buy_balance": "الرصيد الحالي: <b>{balance} رصيد</b>",
        "buy_provider_momo": "💳 الدفع عبر MoMo",
        "buy_provider_stripe": "💳 الدفع عبر Stripe (بطاقة)",
        "buy_provider_manual": "🏦 تحويل يدوي — يؤكده المشرف بعد الاستلام",
        "buy_success": "🎉 تمت إضافة <b>+{credits} رصيد</b>!\nالرصيد الجديد: <b>{balance}</b>.",
        "buy_error": "⚠️ خطأ في الدفع. يرجى المحاولة مرة أخرى أو التواصل مع المشرف.",
    },
}

# Merge extra keys into existing lang dicts (per-key, not replace)
for _lang, _extras in _EXTRA_LANGS.items():
    if _lang in LANG_DICT:
        LANG_DICT[_lang].update(_extras)
    else:
        LANG_DICT[_lang] = _extras
