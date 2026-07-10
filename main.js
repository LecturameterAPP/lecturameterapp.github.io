// ─── Lecturameter web · JS compartido ───

// ─── EMAILJS ───
const EJS_PUBLIC_KEY   = '3cdH3XtjBWBRKC9tS';
const EJS_SERVICE_ID   = 'service_l1psqa9';
const EJS_TPL_VICTOR   = 'template_nlxdksn';
const EJS_TPL_USER     = 'template_pmpiafh';
if (typeof emailjs !== 'undefined') {
    try { emailjs.init(EJS_PUBLIC_KEY); } catch(e) { console.warn('EmailJS init error:', e); }
}

// ─── CAPTCHA ───
// Genera una pregunta aritmética en el elemento indicado (por id).
function newCaptcha(questionId) {
    const a = Math.floor(Math.random() * 9) + 1;
    const b = Math.floor(Math.random() * 9) + 1;
    const questionEl = document.getElementById(questionId);
    if (questionEl) {
        questionEl.textContent = a + ' + ' + b + ' = ?';
        questionEl.dataset.answer = String(a + b);
    }
}

// Comprueba la respuesta; si falla, regenera la pregunta y limpia el input.
function checkCaptcha(questionId, inputId) {
    const questionEl = document.getElementById(questionId);
    const inputEl = document.getElementById(inputId);
    if (!questionEl || !inputEl) return true;
    if (inputEl.value.trim() === questionEl.dataset.answer) return true;
    newCaptcha(questionId);
    inputEl.value = '';
    return false;
}

function generateCaptcha(lang) {
    newCaptcha('captchaQuestion' + (lang === 'es' ? 'Es' : 'En'));
}

// ─── NOTIFY ───
async function sendNotify(lang) {
    const prefix = lang === 'es' ? 'Es' : 'En';
    const email  = document.getElementById('notifyEmail' + prefix).value.trim();
    const captchaInput = document.getElementById('captchaInput' + prefix).value.trim();
    const status = document.getElementById('notifyStatus' + prefix);
    const btn    = document.getElementById('notifyBtn' + prefix);

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        status.textContent = lang === 'es' ? '⚠️ Email no válido' : '⚠️ Invalid email';
        status.className = 'notify-status err';
        return;
    }

    if (!checkCaptcha('captchaQuestion' + prefix, 'captchaInput' + prefix)) {
        status.textContent = lang === 'es' ? '⚠️ Respuesta incorrecta, intenta de nuevo' : '⚠️ Wrong answer, try again';
        status.className = 'notify-status err';
        return;
    }

    btn.disabled = true;
    status.textContent = lang === 'es' ? '⏳ Enviando...' : '⏳ Sending...';
    status.className = 'notify-status loading';

    if (typeof emailjs === 'undefined') {
        status.textContent = lang === 'es' ? '❌ Error. Prueba en lecturameter.app@gmail.com' : '❌ Error. Try lecturameter.app@gmail.com';
        status.className = 'notify-status err';
        btn.disabled = false;
        generateCaptcha(lang);
        return;
    }

    try {
        await emailjs.send(EJS_SERVICE_ID, EJS_TPL_VICTOR, { user_email: email, platforms: 'Play Store' });
        await emailjs.send(EJS_SERVICE_ID, EJS_TPL_USER,   { user_email: email, platforms: 'Play Store' });

        status.textContent = lang === 'es'
            ? '✅ ¡Añadido! Recibirás un correo cuando la app esté lista.'
            : '✅ Added! You\'ll receive an email when the app is ready.';
        status.className = 'notify-status ok';
        document.getElementById('notifyEmail' + prefix).value = '';
        document.getElementById('captchaInput' + prefix).value = '';
        generateCaptcha(lang);
    } catch (e) {
        console.error('EmailJS error:', e);
        status.textContent = lang === 'es'
            ? '❌ Error al enviar. Prueba en lecturameter.app@gmail.com'
            : '❌ Failed to send. Try lecturameter.app@gmail.com';
        status.className = 'notify-status err';
    } finally {
        btn.disabled = false;
    }
}

// ─── FEEDBACK con Formspree ───
async function sendFeedback(lang) {
    const name    = document.getElementById('fbName-' + lang).value.trim();
    const message = document.getElementById('fbMsg-' + lang).value.trim();
    const status  = document.getElementById('fbStatus-' + lang);
    const btn     = document.querySelector('#feedbackForm-' + lang + ' .fb-btn');

    if (!message) {
        status.textContent = lang === 'es' ? '⚠️ Escribe un mensaje' : '⚠️ Please write a message';
        status.className = 'fb-status err';
        return;
    }

    if (!checkCaptcha('captchaQuestionFb-' + lang, 'captchaInputFb-' + lang)) {
        status.textContent = lang === 'es' ? '⚠️ Respuesta incorrecta, intenta de nuevo' : '⚠️ Wrong answer, try again';
        status.className = 'fb-status err';
        return;
    }

    btn.disabled = true;
    status.textContent = lang === 'es' ? '⏳ Enviando...' : '⏳ Sending...';
    status.className = 'fb-status';

    try {
        const res = await fetch('https://formspree.io/f/mgojjnyj', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                name: name || (lang === 'es' ? 'Anónimo' : 'Anonymous'),
                message: message,
                _subject: 'Feedback Lecturameter'
            })
        });

        const data = await res.json();

        if (res.ok) {
            status.textContent = lang === 'es' ? '✅ ¡Enviado! Gracias.' : '✅ Sent! Thank you.';
            status.className = 'fb-status ok';
            document.getElementById('fbName-' + lang).value = '';
            document.getElementById('fbMsg-' + lang).value = '';
            const fbCaptchaInput = document.getElementById('captchaInputFb-' + lang);
            if (fbCaptchaInput) { fbCaptchaInput.value = ''; newCaptcha('captchaQuestionFb-' + lang); }
        } else {
            throw new Error(data.error || 'Error desconocido');
        }
    } catch (e) {
        console.error('Formspree error:', e);
        status.textContent = lang === 'es'
            ? '❌ Error al enviar. Prueba en lecturameter.app@gmail.com'
            : '❌ Failed to send. Try lecturameter.app@gmail.com';
        status.className = 'fb-status err';
    } finally {
        btn.disabled = false;
    }
}

// ─── DATOS PARA ESTADÍSTICAS ───
const sessionData = [
    { date: '03/06/2026', pages: 19, time: 25, range: '9-27' },
    { date: '05/06/2026', pages: 14, time: 26, range: '28-41' },
    { date: '14/06/2026', pages: 19, time: 26, range: '28-41' },
    { date: '18/06/2026', pages: 18, time: 28, range: '55-72' },
    { date: '24/06/2026', pages: 14, time: 22, range: '73-86' },
    { date: '26/06/2026', pages: 42, time: 65, range: '87-128' },
    { date: '30/06/2026', pages: 28, time: 32, range: '129-156' }
];
const totalPages = sessionData.reduce((s, e) => s + e.pages, 0);
const totalMinutes = sessionData.reduce((s, e) => s + e.time, 0);
const statsHours = Math.floor(totalMinutes / 60);
const statsMins = totalMinutes % 60;
const totalTimeStr = statsHours ? `${statsHours}h ${statsMins}m` : `${statsMins}m`;
const avgPagesSession = (totalPages / sessionData.length).toFixed(1);
const avgPace = (totalPages / totalMinutes).toFixed(1);

function renderStats(lang) {
    const prefix = lang === 'es' ? '-es' : '-en';
    const el = (id) => document.getElementById(id + prefix);
    if (el('totalBooks')) el('totalBooks').textContent = '5';
    if (el('totalSessions')) el('totalSessions').textContent = sessionData.length;
    if (el('totalPages')) el('totalPages').textContent = totalPages;
    if (el('totalTime')) el('totalTime').textContent = totalTimeStr;
    if (el('avgPagesSession')) el('avgPagesSession').textContent = avgPagesSession;
    if (el('avgPace')) el('avgPace').textContent = avgPace;

    const chartContainer = document.getElementById('barChart' + prefix);
    if (!chartContainer) return;
    const dayMap = {};
    sessionData.forEach(s => { dayMap[s.date] = (dayMap[s.date] || 0) + s.pages; });
    const days = Object.keys(dayMap);
    const maxVal = Math.max(...Object.values(dayMap), 1);
    let barsHtml = '';
    days.forEach(day => {
        const val = dayMap[day];
        const height = Math.max(4, (val / maxVal) * 100);
        barsHtml += `
            <div class="bar-item">
                <div class="bar-value">${val}</div>
                <div class="bar" style="height:${height}%;"></div>
                <div class="bar-label">${day.split('/')[0]}/${day.split('/')[1]}</div>
            </div>
        `;
    });
    chartContainer.innerHTML = barsHtml;
}

// ─── IDIOMA (persistente entre páginas) ───
function setLang(lang) {
    document.querySelectorAll('.lang-content').forEach(el => el.classList.remove('active'));
    const content = document.getElementById('content-' + lang);
    if (content) content.classList.add('active');
    document.querySelectorAll('.lang-bar button').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById('btn-' + lang);
    if (btn) btn.classList.add('active');
    document.documentElement.lang = lang;
    try { localStorage.setItem('lm_lang', lang); } catch(e) {}

    // Traducir el menú de navegación
    document.querySelectorAll('.nav-links a[data-es]').forEach(a => {
        a.textContent = lang === 'es' ? a.dataset.es : a.dataset.en;
    });

    renderStats(lang);
}

document.addEventListener('DOMContentLoaded', function() {
    let lang = 'es';
    try { lang = localStorage.getItem('lm_lang') || 'es'; } catch(e) {}
    setLang(lang);
    generateCaptcha('es');
    generateCaptcha('en');
    newCaptcha('captchaQuestionFb-es');
    newCaptcha('captchaQuestionFb-en');
});
