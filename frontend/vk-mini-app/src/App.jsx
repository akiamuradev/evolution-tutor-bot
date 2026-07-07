import bridge from '@vkontakte/vk-bridge';
import { useEffect, useMemo, useRef, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const THEME_STORAGE_KEY = 'evolution-theme';
const API_UNAVAILABLE_TEXT = 'Не удалось подключиться к API. Проверь, что backend запущен, или укажи VITE_API_BASE_URL.';

const QUICK_PROMPTS = [
  'Объясни проще',
  'Дай подсказку',
  'Проверь мой ответ',
];

const PRACTICE_SUBJECTS = [
  { value: '', label: 'Любой предмет' },
  { value: 'math', label: 'Математика' },
  { value: 'russian', label: 'Русский' },
  { value: 'physics', label: 'Физика' },
  { value: 'chemistry', label: 'Химия' },
  { value: 'biology', label: 'Биология' },
  { value: 'informatics', label: 'Информатика' },
  { value: 'english', label: 'Английский' },
  { value: 'social-studies', label: 'Обществознание' },
];

const FALLBACK_ACHIEVEMENTS = [
  {
    id: 'first_step',
    title: 'Первый шаг',
    description: 'Отправить первый учебный вопрос',
    unlocked: true,
  },
  {
    id: 'pythagoras',
    title: 'Теорема в руках',
    description: 'Разобрать задачу по геометрии',
    unlocked: false,
  },
  {
    id: 'self_check',
    title: 'Проверил себя',
    description: 'Решить задание после блока самопроверки',
    unlocked: false,
  },
  {
    id: 'streak_3',
    title: 'Три дня подряд',
    description: 'Заниматься три дня без пропусков',
    unlocked: false,
  },
  {
    id: 'deep_explain',
    title: 'Глубокое понимание',
    description: 'Открыть подробное объяснение',
    unlocked: false,
  },
  {
    id: 'exam_mode',
    title: 'Экзаменационный настрой',
    description: 'Начать подготовку к ОГЭ или ЕГЭ',
    unlocked: false,
  },
];

function getLaunchParams() {
  const search = window.location.search.startsWith('?')
    ? window.location.search.slice(1)
    : window.location.search;
  if (search) {
    return search;
  }

  const hashQuery = window.location.hash.includes('?')
    ? window.location.hash.split('?').slice(1).join('?')
    : '';
  if (hashQuery) {
    return hashQuery;
  }

  if (import.meta.env.DEV) {
    return new URLSearchParams({
      vk_user_id: '900000001',
      vk_app_id: 'local_dev',
      vk_ts: String(Math.floor(Date.now() / 1000)),
    }).toString();
  }

  return '';
}

function formatError(error, reason = '') {
  if (!error) {
    return 'Не удалось получить ответ';
  }
  if (error === 'Failed to fetch' || error === 'Load failed' || error === 'NetworkError') {
    return API_UNAVAILABLE_TEXT;
  }
  if (error === 'rate_limited') {
    return 'Слишком много сообщений подряд. Подожди немного.';
  }
  if (error === 'auth_required') {
    return reason
      ? `Не удалось определить пользователя VK. Причина: ${reason}`
      : 'Не удалось определить пользователя VK.';
  }
  if (error === 'internal_error') {
    return 'Сервер временно не ответил.';
  }
  return error;
}

async function requestJson(url, options) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new Error(API_UNAVAILABLE_TEXT);
  }

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error('API вернул некорректный ответ. Проверь backend или Vite proxy.');
  }

  if (!response.ok || !data.ok) {
    throw new Error(formatError(data.error, data.reason));
  }
  return data;
}

async function apiGet(path, launchParams) {
  const params = new URLSearchParams();
  if (launchParams) {
    params.set('launch_params', launchParams);
  }
  return requestJson(`${API_BASE_URL}${path}?${params.toString()}`);
}

async function apiPost(path, payload) {
  return requestJson(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

function MessageBubble({ message }) {
  return (
    <article className={`message message-${message.role}`}>
      <div className="message-author">
        {message.role === 'assistant' ? 'ЭВО:ЛЮЦИЯ' : 'Ты'}
      </div>
      <div className="message-text">{message.text}</div>
    </article>
  );
}

function getInitialThemeMode() {
  if (typeof window === 'undefined') {
    return 'system';
  }
  const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
  return ['system', 'light', 'dark'].includes(saved) ? saved : 'system';
}

function getSystemTheme() {
  if (typeof window === 'undefined') {
    return 'light';
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function LogoImage({ className, activeTheme }) {
  const src = activeTheme === 'dark' ? '/logo-dark-theme.png' : '/logo-light-theme.png';
  return <img className={className} src={src} alt="" />;
}

function App() {
  const [launchParams, setLaunchParams] = useState('');
  const [vkUser, setVkUser] = useState(null);
  const [text, setText] = useState('');
  const [activeTab, setActiveTab] = useState('chat');
  const [themeMode, setThemeMode] = useState(getInitialThemeMode);
  const [systemTheme, setSystemTheme] = useState(getSystemTheme);
  const [profile, setProfile] = useState(null);
  const [activity, setActivity] = useState(null);
  const [achievements, setAchievements] = useState(FALLBACK_ACHIEVEMENTS);
  const [achievementSummary, setAchievementSummary] = useState({
    unlocked: FALLBACK_ACHIEVEMENTS.filter((achievement) => achievement.unlocked).length,
    total: FALLBACK_ACHIEVEMENTS.length,
    percent: Math.round(
      (FALLBACK_ACHIEVEMENTS.filter((achievement) => achievement.unlocked).length / FALLBACK_ACHIEVEMENTS.length) * 100,
    ),
  });
  const [dataStatus, setDataStatus] = useState('Загрузка данных');
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      text: 'Привет. Напиши задачу или тему, а я помогу разобраться по шагам.',
    },
  ]);
  const [status, setStatus] = useState('Подключение');
  const [isSending, setIsSending] = useState(false);
  const [practiceSubject, setPracticeSubject] = useState('');
  const [practiceTask, setPracticeTask] = useState(null);
  const [practiceAnswer, setPracticeAnswer] = useState('');
  const [practiceResult, setPracticeResult] = useState(null);
  const [practiceStatus, setPracticeStatus] = useState('Выбери предмет и получи задачу');
  const [isPracticeLoading, setIsPracticeLoading] = useState(false);
  const scrollRef = useRef(null);

  const canSend = useMemo(() => text.trim().length > 0 && !isSending, [text, isSending]);
  const unlockedCount = achievementSummary.unlocked;
  const totalAchievements = achievementSummary.total || achievements.length || 1;
  const progressPercent = achievementSummary.percent;
  const activeTheme = themeMode === 'system' ? systemTheme : themeMode;
  const themeLabel = themeMode === 'system' ? 'Система' : themeMode === 'dark' ? 'Темная' : 'Светлая';

  function toggleThemeMode() {
    setThemeMode((current) => {
      if (current === 'system') {
        return 'light';
      }
      if (current === 'light') {
        return 'dark';
      }
      return 'system';
    });
  }

  function useQuickPrompt(prompt) {
    setText((current) => {
      const cleanText = current.trim();
      return cleanText ? `${cleanText}\n\n${prompt}` : prompt;
    });
  }

  async function refreshDashboardData(params = launchParams) {
    if (!params) {
      return;
    }
    setDataStatus('Загрузка данных');
    const [profileData, achievementsData, activityData] = await Promise.all([
      apiGet('/api/profile', params),
      apiGet('/api/achievements', params),
      apiGet('/api/activity', params),
    ]);
    setProfile(profileData.profile);
    setAchievements(achievementsData.achievements);
    setAchievementSummary(achievementsData.summary);
    setActivity(activityData.activity);
    setDataStatus('Данные обновлены');
  }

  useEffect(() => {
    const params = getLaunchParams();
    setLaunchParams(params);

    bridge
      .send('VKWebAppInit')
      .then(() => setStatus('VK Mini App'))
      .catch(() => setStatus('Веб-режим'));

    bridge
      .send('VKWebAppGetUserInfo')
      .then((user) => setVkUser(user))
      .catch(() => setVkUser(null));
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = themeMode;
    root.style.colorScheme = activeTheme;
    window.localStorage.setItem(THEME_STORAGE_KEY, themeMode);
  }, [themeMode, activeTheme]);

  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const updateSystemTheme = () => setSystemTheme(media.matches ? 'dark' : 'light');
    updateSystemTheme();
    media.addEventListener('change', updateSystemTheme);
    return () => media.removeEventListener('change', updateSystemTheme);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, isSending]);

  useEffect(() => {
    if (!launchParams) {
      return;
    }

    let canceled = false;
    async function loadDashboardData() {
      try {
        if (canceled) {
          return;
        }
        await refreshDashboardData(launchParams);
      } catch (error) {
        if (!canceled) {
          setDataStatus(formatError(error.message));
        }
      }
    }

    loadDashboardData();
    return () => {
      canceled = true;
    };
  }, [launchParams]);

  async function sendMessage(event) {
    event.preventDefault();
    const cleanText = text.trim();
    if (!cleanText || isSending) {
      return;
    }

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: cleanText,
    };
    setMessages((items) => [...items, userMessage]);
    setText('');
    setIsSending(true);

    try {
      const data = await apiPost('/api/chat', {
        text: cleanText,
        launch_params: launchParams,
      });

      setMessages((items) => [
        ...items,
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          text: data.text,
        },
      ]);
      refreshDashboardData().catch(() => {});
    } catch (error) {
      setMessages((items) => [
        ...items,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          text: formatError(error.message),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  async function loadPracticeTask(subject = practiceSubject) {
    if (!launchParams || isPracticeLoading) {
      return;
    }
    setIsPracticeLoading(true);
    setPracticeResult(null);
    setPracticeAnswer('');
    setPracticeStatus('Ищу подходящую задачу...');
    try {
      const params = new URLSearchParams();
      params.set('launch_params', launchParams);
      if (subject) {
        params.set('subject', subject);
      }
      const data = await requestJson(`${API_BASE_URL}/api/practice/task?${params.toString()}`);
      setPracticeTask(data.task);
      setPracticeStatus('Задача готова');
    } catch (error) {
      setPracticeTask(null);
      setPracticeStatus(formatError(error.message));
    } finally {
      setIsPracticeLoading(false);
    }
  }

  async function submitPracticeAnswer(event) {
    event.preventDefault();
    const cleanAnswer = practiceAnswer.trim();
    if (!practiceTask || !cleanAnswer || isPracticeLoading) {
      return;
    }
    setIsPracticeLoading(true);
    setPracticeStatus('Проверяю ответ...');
    try {
      const data = await apiPost('/api/practice/answer', {
        launch_params: launchParams,
        task_id: practiceTask.id,
        answer: cleanAnswer,
      });
      setPracticeResult(data);
      setPracticeStatus(data.correct ? 'Ответ верный' : 'Есть ошибка, посмотри разбор');
      refreshDashboardData().catch(() => {});
    } catch (error) {
      setPracticeStatus(formatError(error.message));
    } finally {
      setIsPracticeLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <LogoImage className="brand-logo" activeTheme={activeTheme} />
          <div>
            <p className="eyebrow">{status}</p>
            <h1>ЭВО:ЛЮЦИЯ</h1>
          </div>
        </div>
        <div className="top-actions">
          <button
            className="theme-switcher"
            type="button"
            onClick={toggleThemeMode}
            aria-label={`Тема приложения: ${themeLabel}`}
            title="Сменить тему"
          >
            <span>Тема</span>
            <strong>{themeLabel}</strong>
          </button>
          <div className="profile-pill">
            {vkUser?.first_name || 'Ученик'}
          </div>
        </div>
      </header>

      <section className="progress-band" aria-label="Прогресс">
        <div>
          <p className="progress-label">Достижения</p>
          <strong>{unlockedCount} из {totalAchievements}</strong>
        </div>
        <div className="progress-track">
          <span style={{ width: `${progressPercent}%` }} />
        </div>
      </section>

      <nav className="tabbar" aria-label="Разделы">
        <button
          className={activeTab === 'chat' ? 'tab-active' : ''}
          type="button"
          onClick={() => setActiveTab('chat')}
        >
          Чат
        </button>
        <button
          className={activeTab === 'achievements' ? 'tab-active' : ''}
          type="button"
          onClick={() => setActiveTab('achievements')}
        >
          Достижения
        </button>
        <button
          className={activeTab === 'practice' ? 'tab-active' : ''}
          type="button"
          onClick={() => setActiveTab('practice')}
        >
          Практика
        </button>
        <button
          className={activeTab === 'profile' ? 'tab-active' : ''}
          type="button"
          onClick={() => setActiveTab('profile')}
        >
          Профиль
        </button>
      </nav>

      {activeTab === 'chat' && (
        <section className="chat-panel" aria-label="Чат">
          <div className="messages">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isSending && (
              <article className="message message-assistant">
                <div className="message-author">ЭВО:ЛЮЦИЯ</div>
                <div className="thinking">
                  <span />
                  <span />
                  <span />
                </div>
              </article>
            )}
            <div ref={scrollRef} />
          </div>

          <form className="composer" onSubmit={sendMessage}>
            <div className="prompt-actions" aria-label="Быстрые запросы">
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => useQuickPrompt(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
            <textarea
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="Напиши задачу или вопрос"
              rows={1}
            />
            <button type="submit" disabled={!canSend}>
              Отправить
            </button>
          </form>
        </section>
      )}

      {activeTab === 'achievements' && (
        <section className="content-panel" aria-label="Достижения">
          <div className="section-heading">
            <p className="eyebrow">Прогресс</p>
            <h2>{progressPercent}% пути открыто</h2>
          </div>

          <div className="achievement-grid">
            {achievements.map((achievement) => (
              <article
                className={`achievement-card ${achievement.unlocked ? 'achievement-open' : 'achievement-locked'}`}
                key={achievement.id}
              >
                <span className="achievement-status">
                  {achievement.unlocked ? 'Открыто' : 'Скрыто'}
                </span>
                <h3>{achievement.emoji ? `${achievement.emoji} ` : ''}{achievement.title}</h3>
                <p>{achievement.description}</p>
                {!achievement.unlocked && achievement.target > 1 && (
                  <div className="mini-progress" aria-label="Прогресс достижения">
                    <span style={{ width: `${achievement.progress || 0}%` }} />
                  </div>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      {activeTab === 'practice' && (
        <section className="content-panel practice-panel" aria-label="Практика">
          <div className="section-heading">
            <p className="eyebrow">Тренировка</p>
            <h2>Решай задачи и пополняй прогресс</h2>
            <p className="section-subline">{practiceStatus}</p>
          </div>

          <div className="practice-controls">
            <select
              value={practiceSubject}
              onChange={(event) => {
                setPracticeSubject(event.target.value);
                setPracticeTask(null);
                setPracticeResult(null);
                setPracticeAnswer('');
              }}
              aria-label="Предмет"
            >
              {PRACTICE_SUBJECTS.map((subject) => (
                <option key={subject.value || 'all'} value={subject.value}>
                  {subject.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => loadPracticeTask()}
              disabled={isPracticeLoading}
            >
              {practiceTask ? 'Новая задача' : 'Получить задачу'}
            </button>
          </div>

          {practiceTask && (
            <article className="practice-task">
              <div className="task-meta">
                <span>{practiceTask.subject_name || 'Предмет'}</span>
                <span>Задание {practiceTask.task_number || '—'}</span>
                <span>{practiceTask.topic || 'Тема не указана'}</span>
              </div>
              <p>{practiceTask.condition}</p>

              <form className="practice-answer" onSubmit={submitPracticeAnswer}>
                <input
                  value={practiceAnswer}
                  onChange={(event) => setPracticeAnswer(event.target.value)}
                  placeholder="Введи свой ответ"
                  disabled={isPracticeLoading}
                />
                <button
                  type="submit"
                  disabled={!practiceAnswer.trim() || isPracticeLoading}
                >
                  Проверить
                </button>
              </form>
            </article>
          )}

          {practiceResult && (
            <article className={`practice-result ${practiceResult.correct ? 'result-correct' : 'result-wrong'}`}>
              <strong>{practiceResult.correct ? 'Правильно' : 'Пока неверно'}</strong>
              <p>
                Твой ответ: {practiceResult.user_answer || '—'}.
                Правильный ответ: {practiceResult.correct_answer || 'не указан'}.
              </p>
              {practiceResult.solution && (
                <details>
                  <summary>Показать решение</summary>
                  <p>{practiceResult.solution}</p>
                </details>
              )}
              {practiceResult.achievements_text && (
                <p className="achievement-toast">{practiceResult.achievements_text}</p>
              )}
            </article>
          )}
        </section>
      )}

      {activeTab === 'profile' && (
        <section className="content-panel" aria-label="Профиль">
          <div className="profile-summary">
            <LogoImage className="profile-logo" activeTheme={activeTheme} />
            <div>
              <p className="eyebrow">Ученик</p>
              <h2>{vkUser?.first_name || 'Гость'}</h2>
              <p className="profile-subline">{dataStatus}</p>
            </div>
          </div>

          <div className="stat-grid">
            <article className="stat-card">
              <span>Достижения</span>
              <strong>{unlockedCount}/{totalAchievements}</strong>
            </article>
            <article className="stat-card">
              <span>Запросов</span>
              <strong>{profile?.total_requests ?? messages.filter((message) => message.role === 'user').length}</strong>
            </article>
            <article className="stat-card">
              <span>Класс</span>
              <strong>{profile?.grade || '5-9'}</strong>
            </article>
          </div>

          <div className="profile-note">
            <strong>Активность</strong>
            <p>
              Сегодня: {activity?.today_text || '0 мин'}.
              Всего: {activity?.total_text || '0 мин'}.
              Лучшая сессия: {activity?.longest_text || '0 мин'}.
            </p>
          </div>
        </section>
      )}
    </main>
  );
}

export default App;
