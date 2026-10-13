import React from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import sun from "./assets/sun.png";
import house from "./assets/house.png";
import * as api from "./api.js";
import AdminDashboard from "./AdminDashboard.jsx";
import BrandLogo from "./BrandLogo.jsx";
import { formatProductCount } from "./formatters.js";
import ProductVisual from "./ProductVisual.jsx";
import cleanserBottle from "./assets/figma/cleanser-bottle.png";
import cosmeticBag from "./assets/figma/cosmetic-bag.png";
import creamJar from "./assets/figma/cream-jar.png";
import pumpBottle from "./assets/figma/pump-bottle.png";
import routineSet from "./assets/figma/routine-set.png";
import routineShield from "./assets/figma/routine-shield.png";
import spfTube from "./assets/figma/spf-tube.png";
import tableMirror from "./assets/figma/table-mirror.png";
import tonerBottle from "./assets/figma/toner-bottle.png";
import {
  appendExclusiveCustomValue,
  buildRecommendationRequest,
  toggleExclusiveMulti,
  toggleExclusiveStructuredChoice,
  visibleQuestionnaireQuestions,
} from "./questionnaire.js";

/* ==================== decorative bits ==================== */
const QUESTION_ARTWORK = {
  skin_type: cosmeticBag,
  diagnostic_after_cleansing: tableMirror,
  diagnostic_midday_shine: tonerBottle,
  diagnostic_pore_visibility: tableMirror,
  diagnostic_flaking: creamJar,
  concerns: pumpBottle,
  primary_concern: pumpBottle,
  sensitivity_level: creamJar,
  budget: routineSet,
  restrictions: creamJar,
  experience: cleanserBottle,
  routine_preference: routineShield,
  texture_preference: tonerBottle,
  values: spfTube,
  age: cleanserBottle,
};

function QuizArtwork({ questionId, className = "" }) {
  return (
    <img
      className={`figmaArtwork ${className}`.trim()}
      src={QUESTION_ARTWORK[questionId] || routineSet}
      alt=""
      aria-hidden="true"
    />
  );
}

function Flower({ size = 30, className }) {
  const c = 50;
  const petals = [0, 72, 144, 216, 288];
  return (
    <svg
      className={"flower " + (className || "")}
      width={size}
      height={size}
      viewBox="0 0 100 100"
      aria-hidden="true"
    >
      {petals.map((a, i) => (
        <ellipse
          key={i}
          cx={c}
          cy={c - 26}
          rx={15}
          ry={22}
          fill="var(--petal)"
          transform={"rotate(" + a + " " + c + " " + c + ")"}
        />
      ))}
      <circle cx={c} cy={c} r={13} fill="var(--pcenter)" />
    </svg>
  );
}

function Heart({ size = 18, className }) {
  return (
    <svg
      className={"heart " + (className || "")}
      width={size}
      height={size}
      viewBox="0 0 32 30"
      aria-hidden="true"
    >
      <path
        d="M16 28C6 20 1 14 1 8.5 1 4.4 4.4 1 8.5 1 11.6 1 14.3 2.8 16 5.6 17.7 2.8 20.4 1 23.5 1 27.6 1 31 4.4 31 8.5 31 14 26 20 16 28Z"
        fill="#f79ec1"
      />
    </svg>
  );
}

function Cloud({ w = 160, className }) {
  return (
    <svg
      className={"cloud " + (className || "")}
      width={w}
      viewBox="0 0 220 110"
      aria-hidden="true"
    >
      <g fill="var(--cloud)">
        <circle cx="60" cy="72" r="38" />
        <circle cx="104" cy="52" r="48" />
        <circle cx="152" cy="66" r="42" />
        <circle cx="188" cy="80" r="26" />
        <rect x="52" y="74" width="146" height="34" rx="17" />
      </g>
    </svg>
  );
}

function Waves() {
  return (
    <svg
      className="wavesSvg"
      viewBox="0 0 1440 230"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="wgrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#fde4ef" />
          <stop offset="1" stopColor="#f9d0e1" />
        </linearGradient>
      </defs>
      <path
        fill="url(#wgrad)"
        d="M0 70 C240 20 420 110 720 80 C1020 50 1200 120 1440 70 L1440 230 L0 230 Z"
      />
      <path
        fill="var(--wave2)"
        opacity="0.85"
        d="M0 120 C260 70 440 150 720 120 C1000 90 1220 160 1440 110 L1440 230 L0 230 Z"
      />
      <path
        fill="var(--wave3)"
        opacity="0.9"
        d="M0 165 C260 130 480 195 720 165 C980 132 1220 195 1440 160 L1440 230 L0 230 Z"
      />
    </svg>
  );
}

/* ==================== data / helpers ==================== */
/* Questionnaire is now loaded dynamically from the backend
   (GET /api/v1/questionnaire). Product routines come from
   POST /api/v1/recommendations. Only small display helpers live here. */

const STEP_LABEL = {
  cleanser: "Очищение",
  toner: "Тонизация",
  serum: "Сыворотка",
  treatment: "Активный уход",
  moisturizer: "Крем",
  spf: "Защита SPF",
  exfoliation: "Эксфолиация",
  mask: "Маска",
};

const SLOT_LABEL = { morning: "Утро", evening: "Вечер" };

const FEEDBACK_REASONS = [
  { v: "too_expensive", t: "Слишком дорого" },
  { v: "dislikes_brand", t: "Не нравится бренд" },
  { v: "composition_concern", t: "Смущает состав" },
  { v: "texture_not_suitable", t: "Не подходит текстура" },
  { v: "too_many_steps", t: "Слишком много шагов" },
  { v: "other", t: "Другое" },
];

function stepLabel(step) {
  return STEP_LABEL[step] || step;
}

function optionLabel(question, value) {
  const opt = (question.options || []).find((o) => o.value === value);
  return opt ? opt.label : value;
}

function suggestionLabel(question, key) {
  const s = (question.popular_suggestions || []).find(
    (x) => x.canonical_key === key,
  );
  return s ? s.display_name : key;
}

// STEP 3.2 PROFILE_SYNC_HELPERS
function profilePayloadFromAnswers(answers) {
  const request = buildRecommendationRequest(answers);

  return {
    age: request.age,
    skin_type: request.skin_type || null,
    concerns: request.concerns || [],
    primary_concern: request.primary_concern || null,
    sensitivity_level: request.sensitivity_level || null,
    budget: request.budget || null,
    excluded_ingredients: request.excluded_ingredients || [],
    custom_restrictions: request.custom_restrictions || [],
    experience: request.experience || null,
    routine_preference: request.routine_preference || null,
    texture_preference: request.texture_preference || null,
    values: request.values || [],
  };
}

function normalizeEmail(value) {
  return value.trim().toLowerCase();
}

function authErrorMessage(error) {
  if (!error) return null;
  if (error.status === 401) return "Неверная почта или пароль.";
  if (error.status === 409) return "Пользователь с такой почтой уже есть.";
  if (error.status === 422) return "Проверь почту и пароль.";
  return error.message || "Не удалось выполнить действие.";
}

function profileLabel(value) {
  const labels = {
    normal: "Нормальная",
    oily: "Жирная",
    dry: "Сухая",
    combination: "Комбинированная",
    sensitive: "Чувствительная",
    acne: "Высыпания",
    sebum: "Жирный блеск",
    dryness: "Сухость",
    dehydration: "Обезвоженность",
    reactivity: "Реактивность",
    pigmentation: "Пигментация",
    balanced: "Сбалансированный",
    minimum: "Минимальный",
    premium: "Премиум",
  };
  if (Array.isArray(value)) {
    return value.length
      ? value.map((item) => labels[item] || item).join(", ")
      : "—";
  }
  return labels[value] || value || "—";
}

// Flatten morning + evening routine into a unique product list (for pickers).
function uniqueRoutineItems(recommendation) {
  if (!recommendation || !recommendation.routine) return [];
  const seen = new Set();
  const items = [];
  for (const slot of ["morning", "evening"]) {
    for (const item of recommendation.routine[slot] || []) {
      if (seen.has(item.product.external_id)) continue;
      seen.add(item.product.external_id);
      items.push(item);
    }
  }
  return items;
}

/* ==================== shared small components ==================== */
function CenterInfo({ title, text, action }) {
  return (
    <div className="quizPage">
      <div className="quizMain wide" style={{ textAlign: "center" }}>
        {title ? <h1>{title}</h1> : null}
        {text ? <p className="qsub">{text}</p> : null}
        {action ? (
          <div
            className="navRow"
            style={{ justifyContent: "center", marginTop: 16 }}
          >
            <button className="btn solid" onClick={action.on}>
              {action.label}
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function ErrorNote({ message }) {
  if (!message) return null;
  return (
    <div className="okNote" style={{ background: "#fde8ef", color: "#b23a6b" }}>
      {message}
    </div>
  );
}

/* ==================== landing ==================== */
function Landing({ go }) {
  const [activeSection, setActiveSection] = React.useState("");
  const [headerScrolled, setHeaderScrolled] = React.useState(false);
  const [scrollProgress, setScrollProgress] = React.useState(0);

  const scrollTo = (id) =>
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  React.useEffect(() => {
    let frame = 0;
    const updateScrollState = () => {
      if (frame) return;
      frame = window.requestAnimationFrame(() => {
        const scrollable = Math.max(
          1,
          document.documentElement.scrollHeight - window.innerHeight,
        );
        setHeaderScrolled(window.scrollY > 16);
        setScrollProgress(Math.min(1, Math.max(0, window.scrollY / scrollable)));
        frame = 0;
      });
    };

    updateScrollState();
    window.addEventListener("scroll", updateScrollState, { passive: true });
    return () => {
      window.removeEventListener("scroll", updateScrollState);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, []);

  React.useEffect(() => {
    const sections = ["about", "how-it-works", "technology"]
      .map((id) => document.getElementById(id))
      .filter(Boolean);
    if (!sections.length || !("IntersectionObserver" in window)) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => right.intersectionRatio - left.intersectionRatio)[0];
        if (visible) setActiveSection(visible.target.id);
      },
      { rootMargin: "-24% 0px -58%", threshold: [0.08, 0.25, 0.5] },
    );
    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, []);

  return (
    <div className="landing">
      <header
        className={`topbar landingHeader ${headerScrolled ? "scrolled" : ""}`.trim()}
      >
        <BrandLogo onClick={() => go("home")} />
        <nav className="topnav">
          <button
            className={`navpill ${activeSection === "about" ? "active" : ""}`.trim()}
            onClick={() => scrollTo("about")}
            aria-current={activeSection === "about" ? "location" : undefined}
          >
            Подробнее о нас
          </button>
          <button
            className={`navpill ${activeSection === "how-it-works" ? "active" : ""}`.trim()}
            onClick={() => scrollTo("how-it-works")}
            aria-current={activeSection === "how-it-works" ? "location" : undefined}
          >
            Как это работает
          </button>
          <button
            className={`navpill ${activeSection === "technology" ? "active" : ""}`.trim()}
            onClick={() => scrollTo("technology")}
            aria-current={activeSection === "technology" ? "location" : undefined}
          >
            Наши технологии
          </button>
        </nav>
        <button className="navpill vhod" onClick={() => go("login")}>
          вход
        </button>
        <span
          className="landingScrollProgress"
          style={{ transform: `scaleX(${scrollProgress})` }}
          aria-hidden="true"
        />
      </header>

      <section className="hero">
        <Cloud w={150} className="hc hc1" />
        <Cloud w={110} className="hc hc2" />
        <div className="heroInner">
          <div className="heroText">
            <h1>
              Разберёмся с<br />
              уходом вместе
            </h1>
            <p>
              Поделись, что беспокоит кожу — KOYASH бережно подберёт уход и
              объяснит каждый выбор.
            </p>
            <button className="btn solid lg" onClick={() => go("quiz")}>
              собрать косметичку
            </button>
            <span className="heroNote">10–15 вопросов • около 5 минут</span>
          </div>
          <div className="heroArt">
            <img className="heroSun" src={sun} alt="" />
          </div>
        </div>
        <div className="heroWaves">
          <div className="waveWrap">
            <Waves />
            <Flower size={26} className="wf wf1" />
            <Flower size={22} className="wf wf2" />
            <Flower size={28} className="wf wf3" />
            <Flower size={20} className="wf wf4" />
            <Flower size={24} className="wf wf5" />
            <img className="heroHouse" src={house} alt="" />
          </div>
          <div className="waveHem" />
        </div>
      </section>

      <section className="lsec" id="about">
        <Flower size={34} className="dec d1" />
        <Flower size={26} className="dec d2" />
        <Heart size={18} className="dec dh1" />
        <div className="editorialRow aboutStory">
          <div className="storyCopy">
            <span className="sectionEyebrow">О нас</span>
            <h2 className="secTitle">Уход без догадок и лишних покупок</h2>
            <p className="storyLead">
              KOYASH — личный помощник, который переводит особенности твоей
              кожи в понятный и реалистичный план ухода.
            </p>
            <p className="storyBody">
              Мы сначала проверяем ограничения и совместимость, затем собираем
              базовую косметичку под твой бюджет и объясняем роль каждого
              средства — спокойно, честно и без давления брендов.
            </p>
            <div className="storyPrinciples" aria-label="Принципы KOYASH">
              <span>точно</span>
              <span>понятно</span>
              <span>бережно</span>
            </div>
          </div>
          <div className="storyIllustration">
            <span className="artHalo" />
            <img
              className="figmaArtwork storyFigmaArt"
              src={routineShield}
              alt=""
              aria-hidden="true"
            />
            <span className="artNote">твоя косметичка, а не чужой шаблон</span>
          </div>
        </div>
      </section>

      <section className="lsec benefitSection">
        <Flower size={30} className="dec d3" />
        <Flower size={24} className="dec d4" />
        <div className="benefitCanvas">
          <div className="benefitHeading">
            <span className="sectionEyebrow">Что ты получишь</span>
            <h2 className="secTitle">Не список банок, а понятную систему</h2>
            <p>
              В подборке видно, что купить сейчас, что можно отложить и почему
              средство вообще оказалось в рекомендации.
            </p>
          </div>
          <ul className="benefitList">
            <li>
              <span className="benefitIndex">01</span>
              <div>
                <strong>Твой профиль кожи</strong>
                <p>Тип, чувствительность, цели и ограничения в одном месте.</p>
              </div>
            </li>
            <li>
              <span className="benefitIndex">02</span>
              <div>
                <strong>Готовая рутина</strong>
                <p>Средства разложены по этапам и приоритету покупки.</p>
              </div>
            </li>
            <li>
              <span className="benefitIndex">03</span>
              <div>
                <strong>Объяснение выбора</strong>
                <p>Компоненты, польза и способ применения без сложных слов.</p>
              </div>
            </li>
            <li>
              <span className="benefitIndex">04</span>
              <div>
                <strong>Контроль бюджета</strong>
                <p>Цена всей косметички и варианты экономии видны сразу.</p>
              </div>
            </li>
          </ul>
        </div>
      </section>

      <section className="lsec" id="how-it-works">
        <span className="sectionEyebrow centered">Три простых шага</span>
        <h2 className="secTitle center">Как это работает</h2>
        <ol className="processRail">
          <li>
            <span className="processNumber">01</span>
            <h3>Рассказываешь о коже</h3>
            <p>
              Отвечаешь на короткие понятные вопросы. Если не знаешь тип кожи,
              мы поможем определить его по ощущениям.
            </p>
          </li>
          <li>
            <span className="processNumber">02</span>
            <h3>Получаешь безопасный отбор</h3>
            <p>
              Правила исключают неподходящие составы и собирают совместимую
              рутину под твои цели и бюджет.
            </p>
          </li>
          <li>
            <span className="processNumber">03</span>
            <h3>Понимаешь каждый выбор</h3>
            <p>
              Видишь аргументы, способ применения и можешь заменить средство,
              если оно не подходит по цене или ощущениям.
            </p>
          </li>
        </ol>
      </section>

      <section className="lsec">
        <Flower size={30} className="dec d5" />
        <Flower size={24} className="dec d6" />
        <div className="secRow trust">
          <img
            className="figmaArtwork landingPanelArtwork safetyArtwork"
            src={cosmeticBag}
            alt=""
            aria-hidden="true"
          />
          <div className="cloudBox">
            <span className="sectionEyebrow">Почему нам можно доверять</span>
            <h2 className="secTitle">Сначала безопасность. Потом всё остальное.</h2>
            <ul className="daisyList">
              <li>
                <Flower size={22} />
                <span>
                  Каждая рекомендация основывается на анализе состава средств,
                  исследованиях и особенностях твоей кожи.
                </span>
              </li>
              <li>
                <Flower size={22} />
                <span>
                  Цель — найти подходящий уход, а не продать дорогие средства.
                </span>
              </li>
              <li>
                <Flower size={22} />
                <span>
                  Учитываются бюджет, проблемы кожи, предпочтения и ограничения.
                </span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <section className="lsec" id="technology">
        <Flower size={30} className="dec d7" />
        <Heart size={16} className="dec dh2" />
        <span className="sectionEyebrow">Наши технологии</span>
        <h2 className="secTitle">Рекомендации, которые можно проверить</h2>
        <div className="secRow tech">
          <div className="techBox">
            KOYASH использует собственную проверяемую систему анализа составов.
            Она сначала исключает несовместимые средства, а затем собирает уход
            по твоим ответам. Искусственный интеллект может сделать объяснение
            понятнее, но никогда не меняет правила безопасности и сам не выбирает
            продукты.
            <Heart size={16} className="inl" />
          </div>
          <img
            className="figmaArtwork landingPanelArtwork technologyArtwork"
            src={routineSet}
            alt=""
            aria-hidden="true"
          />
        </div>
      </section>

      <section className="lsec">
        <Flower size={30} className="dec d8" />
        <Flower size={22} className="dec d9" />
        <div className="secRow important">
          <div className="cloudCluster left">
            <Cloud w={210} className="cc cc3" />
            <Cloud w={150} className="cc cc4" />
          </div>
          <div className="importantText">
            <h2 className="secTitle">Важно знать!</h2>
            <div className="dashDivider" />
            <p>
              Рекомендации носят информационный характер. Сервис не заменяет
              консультацию дерматолога. При наличии заболеваний кожи стоит
              обратиться к специалисту.
            </p>
          </div>
        </div>
      </section>

      <section className="lsec originSection">
        <div className="originMark" aria-hidden="true">
          <span>Кояшым</span>
          <Heart size={18} />
        </div>
        <div className="originCopy">
          <span className="sectionEyebrow">Немного личного</span>
          <h2 className="secTitle">Название, в котором уже есть забота</h2>
          <p className="originLead">
            Koyash родилось от татарского «кояшым» — «солнышко моё».
          </p>
          <p>
            А логотип основан на настоящем почерке бабушки. Поэтому сервис
            выглядит не как безликая витрина, а как тёплый помощник рядом.
          </p>
        </div>
      </section>

      <div className="footerCta">
        <div>
          <span className="sectionEyebrow centered">Начнём с твоей кожи</span>
          <h2>Соберём уход, который хочется соблюдать</h2>
        </div>
        <button className="btn solid lg" onClick={() => go("quiz")}>
          собрать косметичку
        </button>
      </div>
      <div className="footerWaves">
        <div className="waveWrap">
          <Waves />
          <Flower size={24} className="wf wf1" />
          <Flower size={26} className="wf wf3" />
          <Flower size={22} className="wf wf5" />
        </div>
        <div className="waveHem" />
      </div>
    </div>
  );
}

/* ==================== quiz (dynamic) ==================== */
function Quiz({ go, questionnaire, answers, setAnswers }) {
  const questions = visibleQuestionnaireQuestions(questionnaire, answers);
  const [i, setI] = React.useState(0);
  const [customText, setCustomText] = React.useState("");
  const [skinDiagnosis, setSkinDiagnosis] = React.useState(null);
  const [diagnosisBusy, setDiagnosisBusy] = React.useState(false);
  const [diagnosisError, setDiagnosisError] = React.useState("");

  if (!questions.length) return <CenterInfo text="Загружаем вопросы…" />;

  const q = questions[i];
  const cur = answers[q.id];
  const pct = Math.round(((i + 1) / questions.length) * 100);
  const isMulti = q.answer_type === "multi";
  const isCustom = q.answer_type === "multi_with_custom";
  const isNumber = q.answer_type === "number";
  const custom =
    cur && typeof cur === "object" ? cur : { selected: [], custom: [] };
  const dependencyAnswer = q.depends_on_question_id
    ? answers[q.depends_on_question_id]
    : null;
  const visibleOptions =
    q.depends_on_question_id && Array.isArray(dependencyAnswer)
      ? (q.options || []).filter((option) =>
          dependencyAnswer.includes(option.value),
        )
      : q.options || [];

  const recordAnswer = () =>
    api.trackEvent("question_answered", { metadata: { question_id: q.id } });
  const pickSingle = (v) => {
    setAnswers({ ...answers, [q.id]: v });
    if (q.id.startsWith("diagnostic_") || q.id === "skin_type") {
      setSkinDiagnosis(null);
      setDiagnosisError("");
    }
    recordAnswer();
  };
  const setNumber = (v) => setAnswers({ ...answers, [q.id]: v });
  const toggleMulti = (v) => {
    const nextArr = toggleExclusiveMulti(cur, v, q.max_selections);
    const nextAnswers = { ...answers, [q.id]: nextArr };
    if (
      q.id === "concerns" &&
      answers.primary_concern &&
      !nextArr.includes(answers.primary_concern)
    ) {
      nextAnswers.primary_concern = undefined;
    }
    setAnswers(nextAnswers);
    recordAnswer();
  };
  const toggleSuggestion = (key) => {
    const nextValue = toggleExclusiveStructuredChoice(
      custom,
      key,
      q.max_selections,
    );
    setAnswers({
      ...answers,
      [q.id]: nextValue,
    });
    recordAnswer();
  };
  const addCustom = () => {
    const value = customText.trim();
    if (!value) return;
    const nextValue = appendExclusiveCustomValue(
      custom,
      value,
      q.max_selections,
    );
    if (nextValue.custom.length === custom.custom.length) {
      return;
    }
    setAnswers({
      ...answers,
      [q.id]: nextValue,
    });
    setCustomText("");
    recordAnswer();
  };
  const removeCustom = (value) =>
    setAnswers({
      ...answers,
      [q.id]: {
        selected: custom.selected,
        custom: custom.custom.filter((x) => x !== value),
      },
    });

  const numberValue = isNumber ? Number.parseInt(String(cur || ""), 10) : null;
  const numberFilled =
    isNumber &&
    Number.isFinite(numberValue) &&
    (q.min_value == null || numberValue >= q.min_value) &&
    (q.max_value == null || numberValue <= q.max_value);

  const minimumSelections = q.min_selections || (q.required ? 1 : 0);
  const filled = isMulti
    ? Array.isArray(cur) && cur.length >= minimumSelections
    : isCustom
      ? true
      : isNumber
        ? cur
          ? numberFilled
          : !q.required
        : q.required
          ? !!cur
          : true;

  const next = async () => {
    if (
      q.id === "diagnostic_flaking" &&
      answers.skin_type === "unknown" &&
      !skinDiagnosis
    ) {
      setDiagnosisBusy(true);
      setDiagnosisError("");
      try {
        const result = await api.diagnoseSkin({
          after_cleansing: answers.diagnostic_after_cleansing,
          midday_shine: answers.diagnostic_midday_shine,
          pore_visibility: answers.diagnostic_pore_visibility,
          flaking: answers.diagnostic_flaking,
        });
        setSkinDiagnosis(result);
      } catch (error) {
        setDiagnosisError(
          error.message || "Не удалось определить тип кожи. Попробуй ещё раз.",
        );
        setDiagnosisBusy(false);
        return;
      }
      setDiagnosisBusy(false);
    }
    if (i < questions.length - 1) setI(i + 1);
    else go("review");
  };
  const back = () => {
    if (i > 0) setI(i - 1);
    else go("home");
  };
  const renderRestrictionSuggestion = (suggestion, neutral = false) => {
    const on = custom.selected.includes(suggestion.canonical_key);
    return (
      <button
        key={suggestion.canonical_key}
        className={`opt${neutral ? " neutralOption" : ""}${on ? " sel" : ""}`}
        aria-pressed={on}
        onClick={() => toggleSuggestion(suggestion.canonical_key)}
      >
        <span className="optHead">
          {suggestion.display_name}
          {on ? <span className="check">✓</span> : null}
        </span>
      </button>
    );
  };

  return (
    <div className="quizPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <BrandLogo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
        <button className="btn ghost xs" onClick={() => go("home")}>
          на главную
        </button>
      </header>
      <div className="stepMeta">
        Шаг {i + 1} из {questions.length}
      </div>
      <div className="progress">
        <span style={{ width: pct + "%" }} />
      </div>
      <div className="quizGrid">
        <div className="quizMain">
          <h1>{q.title}</h1>
          <p className="qsub">{q.description}</p>

          {q.id === "concerns" &&
          answers.skin_type === "unknown" &&
          skinDiagnosis ? (
            <div className="skinDiagnosisReveal" role="status">
              <span>Профиль кожи определён</span>
              <div>
                <strong>
                  Похоже, у тебя {profileLabel(skinDiagnosis.resolved_skin_type).toLowerCase()} кожа
                </strong>
                <b>уверенность {skinDiagnosis.confidence_percent}%</b>
              </div>
              <p>
                {skinDiagnosis.signals?.slice(0, 2).join(" ")} Это ориентир для
                косметического ухода, а не медицинская диагностика.
              </p>
            </div>
          ) : null}

          {isNumber ? (
            <div className="field ageField">
              <label>{q.unit ? "Возраст, " + q.unit : "Ответ"}</label>
              <input
                type="number"
                inputMode="numeric"
                min={q.min_value || undefined}
                max={q.max_value || undefined}
                placeholder={q.input_placeholder || "Введите число"}
                value={cur || ""}
                onChange={(e) => setNumber(e.target.value)}
              />
              {cur && !numberFilled ? (
                <p className="qsub smallWarn">
                  Укажи число от {q.min_value || 0} до {q.max_value || 120}.
                </p>
              ) : null}
            </div>
          ) : isCustom ? (
            <div className="restrictionChoices">
              <div className="opts restrictionPresetGrid">
                {(q.popular_suggestions || [])
                  .filter(
                    (suggestion) =>
                      !["none", "unknown"].includes(
                        suggestion.canonical_key,
                      ),
                  )
                  .map((suggestion) =>
                    renderRestrictionSuggestion(suggestion),
                  )}
              </div>
              <div className="restrictionNeutralBlock">
                <span className="restrictionChoiceLabel">
                  Если точных ограничений нет
                </span>
                <div className="opts restrictionNeutralGrid">
                  {(q.popular_suggestions || [])
                    .filter((suggestion) =>
                      ["none", "unknown"].includes(
                        suggestion.canonical_key,
                      ),
                    )
                    .map((suggestion) =>
                      renderRestrictionSuggestion(suggestion, true),
                    )}
                </div>
                <p className="selectionHint">
                  Эти ответы взаимоисключающие: каждый из них очистит выбранные
                  компоненты и свой вариант.
                </p>
              </div>
            </div>
          ) : (
            <div
              className={
                "opts " +
                (q.options && q.options.length === 3 ? "three" : "two")
              }
            >
              {visibleOptions.map((o) => {
                const on = isMulti
                  ? Array.isArray(cur) && cur.includes(o.value)
                  : cur === o.value;
                const limitReached =
                  isMulti &&
                  !on &&
                  !["unknown", "none"].includes(o.value) &&
                  q.max_selections &&
                  Array.isArray(cur) &&
                  cur.length >= q.max_selections;
                return (
                  <button
                    key={o.value}
                    className={"opt" + (on ? " sel" : "")}
                    disabled={!!limitReached}
                    onClick={() =>
                      isMulti ? toggleMulti(o.value) : pickSingle(o.value)
                    }
                  >
                    <span className="optHead">
                      {o.label}
                      {on ? <span className="check">✓</span> : null}
                    </span>
                    {o.description ? (
                      <span className="optDesc">{o.description}</span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          )}

          {isCustom ? (
            <div className="field" style={{ marginTop: 14 }}>
              <label>Свой вариант</label>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  type="text"
                  placeholder="например, отдушки…"
                  maxLength={q.custom_input_max_length || 100}
                  value={customText}
                  onChange={(e) => setCustomText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") addCustom();
                  }}
                />
                <button className="btn ghost" onClick={addCustom}>
                  Добавить
                </button>
              </div>
              {custom.custom.length ? (
                <div
                  className="chipRow"
                  style={{
                    marginTop: 10,
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 8,
                  }}
                >
                  {custom.custom.map((c) => (
                    <button
                      key={c}
                      className="customRestrictionChip"
                      onClick={() => removeCustom(c)}
                    >
                      {c} <span className="check">×</span>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}

          <div className="navRow">
            <button className="btn ghost" onClick={back}>
              Назад
            </button>
            <button
              className="btn solid"
              onClick={next}
              disabled={!filled || diagnosisBusy}
              style={{ opacity: filled && !diagnosisBusy ? 1 : 0.5 }}
            >
              {diagnosisBusy
                ? "Определяем тип…"
                : i < questions.length - 1
                  ? "Далее"
                  : "К результатам"}
            </button>
          </div>
          <ErrorNote message={diagnosisError} />
        </div>
        <aside className="quizSide">
          <div className="whyBox">
            <h4>Зачем мы спрашиваем</h4>
            <p>{q.why_we_ask}</p>
          </div>
          <QuizArtwork questionId={q.id} className={`questionArt art-${q.id}`} />
        </aside>
      </div>
    </div>
  );
}

function Review({ go, questionnaire, answers }) {
  const questions = visibleQuestionnaireQuestions(questionnaire, answers);
  const renderAnswer = (q) => {
    const v = answers[q.id];
    if (q.answer_type === "number") {
      return v ? String(v) + (q.unit ? " " + q.unit : "") : "—";
    }
    if (q.answer_type === "multi") {
      const arr = Array.isArray(v) ? v : [];
      return arr.length ? arr.map((x) => optionLabel(q, x)).join(", ") : "—";
    }
    if (q.answer_type === "multi_with_custom") {
      const obj = v && typeof v === "object" ? v : { selected: [], custom: [] };
      const parts = [
        ...obj.selected.map((k) => suggestionLabel(q, k)),
        ...obj.custom,
      ];
      return parts.length ? parts.join(", ") : "—";
    }
    return v ? optionLabel(q, v) : "—";
  };
  return (
    <div className="quizPage reviewPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <BrandLogo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
      </header>
      <div className="quizMain reviewMain">
        <div className="reviewHero">
          <div>
            <span className="eyebrow">Перед подбором</span>
            <h1>Проверим всё ещё раз</h1>
            <p className="qsub">
              Если что-то не так, ответы сохранятся — можно спокойно вернуться
              и поправить.
            </p>
          </div>
          <img className="figmaArtwork reviewArtwork" src={routineShield} alt="" />
        </div>
        <div className="reviewGrid">
          {questions.map((q) => (
            <div className="reviewCard" key={q.id}>
              <b>{q.title}</b>
              <span>{renderAnswer(q)}</span>
            </div>
          ))}
        </div>
        <div className="navRow">
          <button
            className="btn ghost"
            onClick={() => go("quiz", { preserveAnswers: true })}
          >
            Назад
          </button>
          <button className="btn solid" onClick={() => go("loading")}>
            Собрать косметичку
          </button>
        </div>
      </div>
    </div>
  );
}

function Loading({
  go,
  answers,
  setAnswers,
  setRecommendation,
  auth,
  setAuth,
}) {
  const steps = [
    "Анализируем тип кожи",
    "Сопоставляем составы средств",
    "Учитываем бюджет и ограничения",
    "Формируем объяснения",
  ];
  const [done, setDone] = React.useState(0);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    let alive = true;
    const payload = buildRecommendationRequest(answers);

    if (!payload.skin_type) {
      setError("Сначала ответьте на вопросы анкеты.");
      return;
    }

    api
      .createRecommendation(payload)
      .then(async (rec) => {
        if (!alive) return;

        setRecommendation(rec);

        if (api.getToken()) {
          try {
            const resolvedAnswers = {
              ...answers,
              skin_type:
                rec.skin_profile?.resolved_skin_type || answers.skin_type,
            };
            const updatedProfile = await api.updateMyProfile(
              profilePayloadFromAnswers(resolvedAnswers),
            );

            if (alive) {
              setAuth((current) => ({
                ...(current || auth || {}),
                profile: updatedProfile,
              }));
            }
          } catch {
            // Не блокируем показ результата, если профиль временно не сохранился.
          }
        }

        setAnswers({});

        setTimeout(() => {
          if (alive) go("results");
        }, 400);
      })
      .catch((e) => {
        if (alive) setError(e.message || "Не удалось собрать подбор.");
      });

    return () => {
      alive = false;
    };
  }, []);

  React.useEffect(() => {
    if (done >= steps.length) return;
    const t = setTimeout(() => setDone((d) => d + 1), 600);
    return () => clearTimeout(t);
  }, [done]);

  if (error) {
    return (
      <CenterInfo
        title="Не удалось собрать подбор"
        text={error}
        action={{ label: "Попробовать снова", on: () => go("review") }}
      />
    );
  }

  return (
    <div className="quizPage loadingPage">
      <BrandLogo onClick={() => go("home")} />
      <div className="loadingLayout">
        <div className="quizMain wide">
          <span className="eyebrow">Почти готово</span>
          <h1>Собираем твою косметичку…</h1>
          <p className="qsub">Проверяем каждый шаг — это займёт пару секунд.</p>
          <div className="loadList">
            {steps.map((s, idx) => (
              <div className={"loadRow" + (idx < done ? " ok" : "")} key={s}>
                <span className="loadMark">
                  {idx < done ? "✓" : <span className="spin" />}
                </span>
                {s}
              </div>
            ))}
          </div>
        </div>
        <div className="loadingArt" aria-hidden="true">
          <span className="loadingHalo" />
          <img className="figmaArtwork loadingArtwork" src={routineShield} alt="" />
          <Flower size={34} className="loadingFlower one" />
          <Flower size={26} className="loadingFlower two" />
        </div>
      </div>
    </div>
  );
}

function RoutineCard({ item, index, openItem }) {
  const p = item.product;
  return (
    <div className="routineCard">
      <ProductVisual product={p} compact />
      <div className="routineHead">
        <span className="routineNum">{index + 1}</span>
        <div>
          <h3>{stepLabel(item.routine_step)}</h3>
          <span className="routineName">
            {p.name} · {p.brand} · {p.price_rub} ₽
          </span>
        </div>
      </div>
      <p>{item.why_here}</p>
      <div className="routineUsage">
        <b>Как использовать</b>
        <span>{item.how_to_use || p.how_to_use}</span>
      </div>
      <div className="routineActions">
        <button className="btn solid sm" onClick={() => openItem(item)}>
          О средстве
        </button>
      </div>
    </div>
  );
}

async function shareOrCopyRoutine(text) {
  if (navigator.share) {
    await navigator.share({ title: "Мой уход KOYASH", text });
    return "Подбор отправлен";
  }
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return "Подбор скопирован";
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  textarea.remove();
  if (!copied) throw new Error("Copy is unavailable");
  return "Подбор скопирован";
}

function Results({
  go,
  auth,
  recommendation,
  openItem,
  replacementNotice,
  clearReplacementNotice,
}) {
  const [shareNotice, setShareNotice] = React.useState("");

  React.useEffect(() => {
    if (!recommendation) return;
    api.trackEvent("result_viewed", {
      recommendation_id: recommendation.recommendation_id,
      metadata: { algorithm_version: recommendation.algorithm_version },
    });
  }, [recommendation?.recommendation_id]);

  React.useEffect(() => {
    if (!replacementNotice) return undefined;
    const timeout = setTimeout(clearReplacementNotice, 5200);
    return () => clearTimeout(timeout);
  }, [replacementNotice, clearReplacementNotice]);

  React.useEffect(() => {
    if (!shareNotice) return undefined;
    const timeout = setTimeout(() => setShareNotice(""), 3600);
    return () => clearTimeout(timeout);
  }, [shareNotice]);

  if (!recommendation) {
    return (
      <CenterInfo
        title="Подбор пока пуст"
        text="Сначала пройдите анкету."
        action={{ label: "К анкете", on: () => go("quiz") }}
      />
    );
  }

  const morning = recommendation.routine.morning || [];
  const evening = recommendation.routine.evening || [];
  const routineProductCount = new Set(
    [...morning, ...evening].map((item) => item.product.external_id),
  ).size;
  const resolvedSkinType = profileLabel(
    recommendation.skin_profile?.resolved_skin_type || "уточнён",
  );
  const confidencePercent = Number(
    recommendation.skin_profile?.confidence_percent,
  );
  const skinProfileNote =
    recommendation.skin_profile?.method === "guided_diagnostic"
      ? Number.isFinite(confidencePercent)
        ? `Определён по ответам · уверенность ${confidencePercent}%`
        : "Определён по уточняющим ответам"
      : "Выбран тобой в анкете";
  const totalPriceRub = Number(recommendation.total_price_rub);
  const formattedTotalPrice = Number.isFinite(totalPriceRub)
    ? `${totalPriceRub.toLocaleString("ru-RU")} ₽`
    : "Стоимость уточняется";
  const shareRoutine = async () => {
    const lines = ["Мой уход KOYASH"];
    if (morning.length) {
      lines.push(
        "Утро: " + morning.map((item) => item.product.name).join(" → "),
      );
    }
    if (evening.length) {
      lines.push(
        "Вечер: " + evening.map((item) => item.product.name).join(" → "),
      );
    }
    lines.push(`Ориентир по сумме: ${recommendation.total_price_rub.toLocaleString("ru-RU")} ₽`);

    try {
      setShareNotice(await shareOrCopyRoutine(lines.join("\n")));
      api.trackEvent("recommendation_shared", {
        recommendation_id: recommendation.recommendation_id,
        metadata: { surface: "results" },
      });
    } catch (error) {
      if (error?.name !== "AbortError") {
        setShareNotice("Не удалось поделиться. Попробуй ещё раз.");
      }
    }
  };

  return (
    <div className="quizPage">
      <header className="topbar resultHeader">
        <BrandLogo onClick={() => go("home")} />
        <nav aria-label="Навигация по подбору">
          <button
            className="btn ghost xs"
            onClick={() => go(auth ? "account" : "login")}
          >
            {auth ? "кабинет" : "войти"}
          </button>
        </nav>
      </header>
      <section className="resultHeroCard">
        <div className="resultHeroCopy">
          <span className="resultEyebrow">Персональная рутина</span>
          <h1 className="resultTitle">Твоя косметичка готова</h1>
          <p>
            Мы собрали понятный уход на утро и вечер — с порядком нанесения,
            инструкциями и объяснением каждого выбора.
          </p>
          <div className="resultHighlights" aria-label="Кратко о подборе">
            <span>{formatProductCount(routineProductCount)}</span>
            <span>утро и вечер</span>
            <span>можно заменить</span>
          </div>
        </div>
        <div className="resultSummaryPanel">
          <div className="resultSummaryMetric resultSummaryTotal">
            <span>Ориентир по стоимости</span>
            <strong>{formattedTotalPrice}</strong>
            <small>за всю косметичку</small>
          </div>
          <div className="resultSummaryDivider" aria-hidden="true" />
          <div className="resultSummaryMetric">
            <span>Профиль кожи</span>
            <strong>{resolvedSkinType}</strong>
            <small>{skinProfileNote}</small>
          </div>
        </div>
      </section>

      {replacementNotice ? (
        <div className="okNote replacementAppliedNote" role="status">
          {replacementNotice}
        </div>
      ) : null}
      {shareNotice ? (
        <div className="okNote replacementAppliedNote" role="status">
          {shareNotice}
        </div>
      ) : null}

      <section className={`resultSavePanel ${auth ? "saved" : "guest"}`}>
        <div>
          <span className="resultEyebrow">
            {auth ? "Сохранено в аккаунте" : "Не потеряй этот уход"}
          </span>
          <h2>
            {auth
              ? "Подбор доступен в истории"
              : "Сохрани подбор после входа"}
          </h2>
          <p>
            {auth
              ? "Можно вернуться к этой версии, увидеть замены и собрать новый вариант."
              : "Мы привяжем уже готовую косметичку к аккаунту — проходить анкету заново не придётся."}
          </p>
        </div>
        <button
          className={auth ? "btn ghost" : "btn solid"}
          onClick={() =>
            auth
              ? go("history")
              : go("login", { returnTo: "results" })
          }
        >
          {auth ? "Открыть историю" : "Войти и сохранить"}
        </button>
      </section>

      {recommendation.filter_summary.restriction_coverage
        ?.unmatched_restrictions?.length ? (
        <div className="notice restrictionNotice">
          Не нашли подтверждённого совпадения для:{" "}
          <b>
            {recommendation.filter_summary.restriction_coverage.unmatched_restrictions.join(
              ", ",
            )}
          </b>
          . Проверь состав на упаковке вручную.
        </div>
      ) : null}

      {morning.length ? (
        <>
          <h2 className="secTitle">Утро</h2>
          <div className="routineGrid">
            {morning.map((it, idx) => (
              <RoutineCard
                key={"m" + it.product.external_id + idx}
                item={it}
                index={idx}
                openItem={openItem}
              />
            ))}
          </div>
        </>
      ) : null}

      {evening.length ? (
        <>
          <h2 className="secTitle">Вечер</h2>
          <div className="routineGrid">
            {evening.map((it, idx) => (
              <RoutineCard
                key={"e" + it.product.external_id + idx}
                item={it}
                index={idx}
                openItem={openItem}
              />
            ))}
          </div>
        </>
      ) : null}

      <div className="navRow">
        <button
          className="btn ghost"
          onClick={() => go("quiz")}
        >
          Пройти заново
        </button>
        <button className="btn solid" onClick={() => go("feedback")}>
          Оценить подбор
        </button>
        <button className="btn ghost" onClick={shareRoutine}>
          Поделиться подбором
        </button>
      </div>
    </div>
  );
}

function ReplacementList({ candidates, onSelect, selectedId, busy }) {
  if (!candidates || !candidates.length) return null;
  return (
    <div style={{ marginTop: 16 }}>
      <h3>Возможные замены</h3>
      <div className="routineGrid">
        {candidates.map((c) => {
          const chosen = selectedId === c.product.external_id;
          return (
            <div className="routineCard replacementCard" key={c.product.external_id}>
              <ProductVisual product={c.product} compact />
              <div className="routineHead">
                <div>
                  <h3>{c.product.name}</h3>
                  <span className="routineName">
                    {c.product.brand} · {c.product.price_rub} ₽
                  </span>
                </div>
              </div>
              <p>{c.why_better}</p>
              <div className="routineUsage">
                <b>Как использовать</b>
                <span>{c.product.how_to_use}</span>
              </div>
              <div className="routineActions">
                <button
                  className={"btn " + (chosen ? "ghost" : "solid") + " sm"}
                  disabled={busy || chosen}
                  onClick={() => onSelect(c)}
                >
                  {chosen ? "Выбрано ✓" : "Выбрать замену"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Product({ go, item, recommendation, onReplacementApplied }) {
  const [reason, setReason] = React.useState("");
  const [comment, setComment] = React.useState("");
  const [result, setResult] = React.useState(null);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [selectedId, setSelectedId] = React.useState(null);

  React.useEffect(() => {
    if (!item?.product?.external_id) return;
    api.trackEvent("product_details_opened", {
      recommendation_id: recommendation?.recommendation_id,
      product_external_id: item.product.external_id,
    });
  }, [item?.product?.external_id]);

  if (!item) {
    return (
      <CenterInfo
        title="Средство не выбрано"
        text="Вернитесь к подбору."
        action={{ label: "К подбору", on: () => go("results") }}
      />
    );
  }

  const p = item.product;

  const send = () => {
    if (!reason || !recommendation) return;
    setBusy(true);
    setError(null);
    api
      .submitFeedback(recommendation.recommendation_id, {
        product_external_id: p.external_id,
        reason,
        comment: comment || null,
      })
      .then((res) => setResult(res))
      .catch((e) => setError(e.message))
      .finally(() => setBusy(false));
  };

  const choose = (candidate) => {
    if (!result) return;
    setBusy(true);
    api
      .selectReplacement(
        recommendation.recommendation_id,
        result.replacement_session_id,
        candidate.product.external_id,
      )
      .then((response) => {
        setSelectedId(candidate.product.external_id);
        onReplacementApplied(response, candidate.product);
      })
      .catch((e) => setError(e.message))
      .finally(() => setBusy(false));
  };

  return (
    <div className="quizPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <BrandLogo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
        <button className="btn ghost xs" onClick={() => go("results")}>
          к подбору
        </button>
      </header>
      <button className="linkBtn prodBack" onClick={() => go("results")}>
        ← Назад к косметичке
      </button>
      <div className="prodTop">
        <div className="prodImg">
          <ProductVisual product={p} />
        </div>
        <div className="prodInfo">
          <div className="prodStep">{stepLabel(item.routine_step)}</div>
          <h1>{p.name}</h1>
          <div className="prodPrice">
            {p.brand} · {p.price_rub} ₽
          </div>
          <p>{item.why_here}</p>
          {item.budget_reason ? (
            <p className="qsub">{item.budget_reason}</p>
          ) : null}
          {item.safety_note ? <p className="qsub">{item.safety_note}</p> : null}
          <div className="routineActions productPrimaryActions">
            {p.product_url ? (
              <a
                className="btn solid"
                href={p.product_url}
                target="_blank"
                rel="noreferrer"
                onClick={() =>
                  api.trackEvent("store_opened", {
                    recommendation_id: recommendation?.recommendation_id,
                    product_external_id: p.external_id,
                    metadata: { surface: "recommendation_product" },
                  })
                }
              >
                Открыть магазин
              </a>
            ) : null}
            <button className="btn ghost" onClick={() => go("results")}>
              Вернуться к подбору
            </button>
          </div>
        </div>
      </div>
      <div className="prodSection">
        <h3>О средстве</h3>
        <p>{p.description}</p>
        {p.ingredients && p.ingredients.length ? (
          <>
            <h3>Состав</h3>
            <ul className="ingList">
              {p.ingredients.map((ing) => (
                <li key={ing}>{ing}</li>
              ))}
            </ul>
          </>
        ) : null}
        <h3>Как использовать</h3>
        <p>{item.how_to_use || p.how_to_use}</p>
      </div>
      <div className="prodFeedback">
        <h3>Не подошло средство?</h3>
        {result ? (
          <>
            <div
              className={
                result.replacement_candidates?.length
                  ? "okNote"
                  : "emptyReplacementNote"
              }
              role="status"
            >
              {result.replacement_message ||
                (result.replacement_candidates?.length
                  ? "Нашли несколько подходящих вариантов."
                  : "Сейчас не нашли подходящую замену.")}
            </div>
            <ErrorNote message={error} />
            <ReplacementList
              candidates={result.replacement_candidates}
              onSelect={choose}
              selectedId={selectedId}
              busy={busy}
            />
            {!result.replacement_candidates?.length ? (
              <div className="routineActions replacementEmptyActions">
                <button className="btn ghost sm" onClick={() => go("results")}>
                  Вернуться к подбору
                </button>
                <button className="btn solid sm" onClick={() => go("quiz")}>
                  Собрать новый подбор
                </button>
              </div>
            ) : null}
          </>
        ) : (
          <>
            <p className="qsub" style={{ marginBottom: 10 }}>
              Расскажи, что не так — подберём альтернативу.
            </p>
            <div className="field">
              <label htmlFor="product-feedback-reason">Причина</label>
              <select
                id="product-feedback-reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              >
                <option value="">Выберите причину…</option>
                {FEEDBACK_REASONS.map((r) => (
                  <option key={r.v} value={r.v}>
                    {r.t}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="product-feedback-comment">Комментарий</label>
              <textarea
                id="product-feedback-comment"
                rows={3}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Необязательно"
              />
            </div>
            <ErrorNote message={error} />
            <button
              className="btn solid"
              onClick={send}
              disabled={!reason || busy}
              style={{ opacity: !reason || busy ? 0.5 : 1 }}
            >
              {busy ? "Отправляем…" : "Подобрать замену"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function Feedback({ go, recommendation, onReplacementApplied }) {
  const items = uniqueRoutineItems(recommendation);
  const [productId, setProductId] = React.useState(
    items.length ? items[0].product.external_id : "",
  );
  const [reason, setReason] = React.useState("");
  const [comment, setComment] = React.useState("");
  const [result, setResult] = React.useState(null);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [selectedId, setSelectedId] = React.useState(null);

  const send = () => {
    if (!recommendation || !productId || !reason) return;
    setBusy(true);
    setError(null);
    api
      .submitFeedback(recommendation.recommendation_id, {
        product_external_id: productId,
        reason,
        comment: comment || null,
      })
      .then((res) => setResult(res))
      .catch((e) => setError(e.message))
      .finally(() => setBusy(false));
  };

  const choose = (candidate) => {
    if (!result) return;
    setBusy(true);
    api
      .selectReplacement(
        recommendation.recommendation_id,
        result.replacement_session_id,
        candidate.product.external_id,
      )
      .then((response) => {
        setSelectedId(candidate.product.external_id);
        onReplacementApplied(response, candidate.product);
      })
      .catch((e) => setError(e.message))
      .finally(() => setBusy(false));
  };

  return (
    <div className="quizPage">
      <div className="quizMain wide">
        <h1>Оцени подбор</h1>
        <p className="qsub">Твой отзыв помогает делать рекомендации точнее.</p>
        {!recommendation ? (
          <CenterInfo
            text="Сначала пройдите анкету и получите подбор."
            action={{ label: "К анкете", on: () => go("quiz") }}
          />
        ) : result ? (
          <>
            <div
              className={
                result.replacement_candidates?.length
                  ? "okNote"
                  : "emptyReplacementNote"
              }
              role="status"
            >
              {result.replacement_message ||
                (result.replacement_candidates?.length
                  ? "Отзыв сохранён — выбери подходящую замену."
                  : "Отзыв сохранён, но подходящей замены сейчас нет.")}
            </div>
            <ErrorNote message={error} />
            <ReplacementList
              candidates={result.replacement_candidates}
              onSelect={choose}
              selectedId={selectedId}
              busy={busy}
            />
            {!result.replacement_candidates?.length ? (
              <div className="routineActions replacementEmptyActions">
                <button className="btn ghost sm" onClick={() => go("results")}>
                  Вернуться к подбору
                </button>
                <button className="btn solid sm" onClick={() => go("quiz")}>
                  Собрать новый подбор
                </button>
              </div>
            ) : null}
          </>
        ) : (
          <>
            <div className="field">
              <label htmlFor="routine-feedback-product">Средство</label>
              <select
                id="routine-feedback-product"
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
              >
                {items.map((it) => (
                  <option
                    key={it.product.external_id}
                    value={it.product.external_id}
                  >
                    {stepLabel(it.routine_step)} — {it.product.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="routine-feedback-reason">Что не так?</label>
              <select
                id="routine-feedback-reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              >
                <option value="">Выберите причину…</option>
                {FEEDBACK_REASONS.map((r) => (
                  <option key={r.v} value={r.v}>
                    {r.t}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="routine-feedback-comment">Комментарий</label>
              <textarea
                id="routine-feedback-comment"
                rows={4}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Что понравилось, а что можно улучшить?"
              />
            </div>
            <ErrorNote message={error} />
            <button
              className="btn solid"
              onClick={send}
              disabled={!reason || busy}
              style={{ opacity: !reason || busy ? 0.5 : 1 }}
            >
              {busy ? "Отправляем…" : "Отправить"}
            </button>
          </>
        )}
        <div className="navRow" style={{ marginTop: 20 }}>
          <button className="btn ghost" onClick={() => go("results")}>
            Назад к подбору
          </button>
          <button className="btn ghost" onClick={() => go("home")}>
            На главную
          </button>
        </div>
      </div>
    </div>
  );
}

function Login({ go, onAuth, returnTo = "account" }) {
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState(null);

  const submit = () => {
    const normalizedEmail = normalizeEmail(email);
    if (!normalizedEmail || !password) {
      setError("Заполни почту и пароль.");
      return;
    }

    setBusy(true);
    setError(null);

    api
      .login(normalizedEmail, password)
      .then((res) => {
        api.setToken(res.access_token);
        onAuth({
          user: res.user,
          profile: res.profile,
          claimed_recommendations: res.claimed_recommendations || 0,
        });
        go(returnTo);
      })
      .catch((e) => setError(authErrorMessage(e)))
      .finally(() => setBusy(false));
  };

  return (
    <div className="quizPage authPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <BrandLogo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
      </header>
      <div className="authCard">
        <h1>Вход</h1>
        <div className="field">
          <label htmlFor="login-email">Почта</label>
          <input
            id="login-email"
            type="email"
            autoComplete="email"
            placeholder="user@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
            }}
          />
        </div>
        <div className="field">
          <label htmlFor="login-password">Пароль</label>
          <input
            id="login-password"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
            }}
          />
        </div>
        <ErrorNote message={error} />
        <button
          className="btn solid"
          style={{ width: "100%" }}
          onClick={submit}
          disabled={busy || !email || !password}
        >
          {busy ? "Входим…" : "Войти"}
        </button>
        <div className="authLinks">
          <button className="linkBtn" onClick={() => go("reset")}>
            Забыли пароль?
          </button>
          <button
            className="linkBtn"
            onClick={() => go("register", { returnTo })}
          >
            Регистрация
          </button>
        </div>
      </div>
    </div>
  );
}

function Register({ go, onAuth, returnTo = "account" }) {
  const [fullName, setFullName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [password2, setPassword2] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState(null);

  const submit = () => {
    const normalizedEmail = normalizeEmail(email);

    if (!normalizedEmail) {
      setError("Укажи почту.");
      return;
    }
    if (password.length < 8) {
      setError("Пароль должен быть не короче 8 символов.");
      return;
    }
    if (password !== password2) {
      setError("Пароли не совпадают.");
      return;
    }

    setBusy(true);
    setError(null);

    api
      .register({
        email: normalizedEmail,
        password,
        full_name: fullName.trim() || null,
      })
      .then((res) => {
        api.setToken(res.access_token);
        onAuth({
          user: res.user,
          profile: res.profile,
          claimed_recommendations: res.claimed_recommendations || 0,
        });
        go(returnTo);
      })
      .catch((e) => setError(authErrorMessage(e)))
      .finally(() => setBusy(false));
  };

  return (
    <div className="quizPage authPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <BrandLogo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
      </header>
      <div className="authCard">
        <h1>Регистрация</h1>
        <div className="field">
          <label htmlFor="register-name">Имя</label>
          <input
            id="register-name"
            type="text"
            autoComplete="name"
            placeholder="Как тебя зовут?"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="register-email">Почта</label>
          <input
            id="register-email"
            type="email"
            autoComplete="email"
            placeholder="user@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="register-password">Пароль</label>
          <input
            id="register-password"
            type="password"
            autoComplete="new-password"
            placeholder="минимум 8 символов"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="register-password-again">Повторите пароль</label>
          <input
            id="register-password-again"
            type="password"
            autoComplete="new-password"
            placeholder="••••••••"
            value={password2}
            onChange={(e) => setPassword2(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
            }}
          />
        </div>
        <ErrorNote message={error} />
        <button
          className="btn solid"
          style={{ width: "100%" }}
          onClick={submit}
          disabled={busy || !email || !password || !password2}
        >
          {busy ? "Создаём…" : "Создать аккаунт"}
        </button>
        <div className="authLinks">
          <button
            className="linkBtn"
            onClick={() => go("login", { returnTo })}
          >
            Уже есть аккаунт? Войти
          </button>
          <button className="linkBtn" onClick={() => go("quiz")}>
            Собрать подбор
          </button>
        </div>
      </div>
    </div>
  );
}

function Reset({ go }) {
  const hashQuery = window.location.hash.includes("?")
    ? window.location.hash.split("?")[1]
    : "";
  const initialToken =
    new URLSearchParams(window.location.search).get("token") ||
    new URLSearchParams(hashQuery).get("token") ||
    "";
  const [email, setEmail] = React.useState("");
  const [tokenValue, setTokenValue] = React.useState(initialToken);
  const [password, setPassword] = React.useState("");
  const [passwordAgain, setPasswordAgain] = React.useState("");
  const [sent, setSent] = React.useState(false);
  const [complete, setComplete] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState("");

  const requestLink = async () => {
    setBusy(true);
    setError("");
    try {
      const result = await api.forgotPassword(email);
      setSent(true);
      if (result.dev_reset_url) {
        const parsed = new URL(result.dev_reset_url, window.location.origin);
        setTokenValue(parsed.searchParams.get("token") || "");
      }
    } catch (requestError) {
      setError(authErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  };

  const savePassword = async () => {
    if (password !== passwordAgain) {
      setError("Пароли не совпадают.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api.resetPassword(tokenValue, password);
      setComplete(true);
    } catch (requestError) {
      setError(authErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="quizPage authPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <BrandLogo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
      </header>
      <div className="authCard">
        <h1>Сброс пароля</h1>
        {complete ? (
          <div className="okNote">
            Пароль обновлён. Все старые сеансы завершены — можно войти заново.
          </div>
        ) : tokenValue ? (
          <>
            <div className="field">
              <label htmlFor="reset-password">Новый пароль</label>
              <input
                id="reset-password"
                type="password"
                autoComplete="new-password"
                minLength={8}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Минимум 8 символов"
              />
            </div>
            <div className="field">
              <label htmlFor="reset-password-again">Повторите пароль</label>
              <input
                id="reset-password-again"
                type="password"
                autoComplete="new-password"
                value={passwordAgain}
                onChange={(event) => setPasswordAgain(event.target.value)}
              />
            </div>
            <ErrorNote message={error} />
            <button
              className="btn solid"
              style={{ width: "100%" }}
              onClick={savePassword}
              disabled={busy || password.length < 8 || !passwordAgain}
            >
              {busy ? "Сохраняем…" : "Обновить пароль"}
            </button>
          </>
        ) : sent ? (
          <div className="okNote">
            Если такая почта есть, мы отправим инструкции по восстановлению.
          </div>
        ) : (
          <>
            <div className="field">
              <label htmlFor="reset-email">Почта</label>
              <input
                id="reset-email"
                type="email"
                autoComplete="email"
                placeholder="user@example.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>
            <ErrorNote message={error} />
            <button
              className="btn solid"
              style={{ width: "100%" }}
              onClick={requestLink}
              disabled={busy || !email}
            >
              {busy ? "Отправляем…" : "Отправить ссылку"}
            </button>
          </>
        )}
        <div className="authLinks">
          <button className="linkBtn" onClick={() => go("login")}>
            Вернуться ко входу
          </button>
        </div>
      </div>
    </div>
  );
}

function Account({ go, auth, setAuth }) {
  const [profile, setProfile] = React.useState(
    auth && auth.profile ? auth.profile : null,
  );
  const [user, setUser] = React.useState(auth && auth.user ? auth.user : null);
  const [loading, setLoading] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [saved, setSaved] = React.useState(false);
  const [recommendationCount, setRecommendationCount] = React.useState(0);
  const [form, setForm] = React.useState({
    full_name: user && user.full_name ? user.full_name : "",
    age: profile && profile.age ? String(profile.age) : "",
    skin_type: profile && profile.skin_type ? profile.skin_type : "",
    budget: profile && profile.budget ? profile.budget : "",
    experience: profile && profile.experience ? profile.experience : "",
    concerns:
      profile && profile.concerns && profile.concerns.length
        ? profile.concerns.join(", ")
        : "",
    values:
      profile && profile.values && profile.values.length
        ? profile.values.join(", ")
        : "",
  });

  React.useEffect(() => {
    if (!api.getToken()) return;

    setLoading(true);
    setError(null);

    api
      .loadAuthState()
      .then((state) => {
        if (!state) return;

        setAuth(state);
        setUser(state.user);
        setProfile(state.profile);
        setForm({
          full_name:
            state.user && state.user.full_name ? state.user.full_name : "",
          age:
            state.profile && state.profile.age ? String(state.profile.age) : "",
          skin_type:
            state.profile && state.profile.skin_type
              ? state.profile.skin_type
              : "",
          budget:
            state.profile && state.profile.budget ? state.profile.budget : "",
          experience:
            state.profile && state.profile.experience
              ? state.profile.experience
              : "",
          concerns:
            state.profile && state.profile.concerns
              ? state.profile.concerns.join(", ")
              : "",
          values:
            state.profile && state.profile.values
              ? state.profile.values.join(", ")
              : "",
        });
      })
      .catch((e) => setError(authErrorMessage(e)))
      .finally(() => setLoading(false));
    api
      .getMyRecommendations(1, 0)
      .then((data) => setRecommendationCount(data.total || 0))
      .catch(() => {});
  }, []);

  const logout = () => {
    api.logout();
    setAuth(null);
    go("home");
  };

  const parseList = (value) =>
    value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

  const save = () => {
    setSaving(true);
    setSaved(false);
    setError(null);

    const age = form.age ? Number.parseInt(form.age, 10) : null;

    if (form.age && (!Number.isFinite(age) || age < 12 || age > 100)) {
      setError("Возраст должен быть числом от 12 до 100.");
      setSaving(false);
      return;
    }

    Promise.all([
      api.updateMe({ full_name: form.full_name.trim() || null }),
      api.updateMyProfile({
        age,
        skin_type: form.skin_type || null,
        budget: form.budget || null,
        experience: form.experience || null,
        concerns: parseList(form.concerns),
        values: parseList(form.values),
      }),
    ])
      .then(([updatedUser, updatedProfile]) => {
        const nextAuth = { user: updatedUser, profile: updatedProfile };
        setUser(updatedUser);
        setProfile(updatedProfile);
        setAuth(nextAuth);
        setSaved(true);
      })
      .catch((e) => setError(authErrorMessage(e)))
      .finally(() => setSaving(false));
  };

  if (!api.getToken()) {
    return (
      <CenterInfo
        title="Нужен вход"
        text="Войдите, чтобы увидеть личный кабинет."
        action={{ label: "Войти", on: () => go("login") }}
      />
    );
  }

  const name = (user && (user.full_name || user.email)) || "друг";
  return (
    <div className="quizPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <BrandLogo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
        <button className="btn ghost xs" onClick={logout}>
          выйти
        </button>
      </header>
      <div className="quizMain wide">
        <h1>Личный кабинет</h1>
        <p className="qsub">
          Привет, {name}! Здесь хранятся профиль кожи и история подборов.
        </p>
        {loading ? <p className="qsub">Загружаем профиль…</p> : null}
        <ErrorNote message={error} />
        {saved ? <div className="okNote">Профиль сохранён.</div> : null}

        <div className="reviewGrid">
          <div className="reviewCard">
            <b>Возраст</b>
            <span>{profile && profile.age ? profile.age + " лет" : "—"}</span>
          </div>
          <div className="reviewCard">
            <b>Тип кожи</b>
            <span>{profileLabel(profile && profile.skin_type)}</span>
          </div>
          <div className="reviewCard">
            <b>Задачи ухода</b>
            <span>{profileLabel(profile && profile.concerns)}</span>
          </div>
          <div className="reviewCard">
            <b>Подборов в истории</b>
            <span>{recommendationCount}</span>
          </div>
        </div>

        <div className="accountForm">
          <div className="field">
            <label>Имя</label>
            <input
              type="text"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              placeholder="Как тебя зовут?"
            />
          </div>
          <div className="field">
            <label>Возраст</label>
            <input
              type="number"
              min="12"
              max="100"
              value={form.age}
              onChange={(e) => setForm({ ...form, age: e.target.value })}
              placeholder="например 19"
            />
          </div>
          <div className="field">
            <label>Тип кожи</label>
            <select
              value={form.skin_type}
              onChange={(e) => setForm({ ...form, skin_type: e.target.value })}
            >
              <option value="">Не указано</option>
              <option value="oily">Жирная</option>
              <option value="dry">Сухая</option>
              <option value="combination">Комбинированная</option>
              <option value="sensitive">Чувствительная</option>
            </select>
          </div>
          <div className="field">
            <label>Бюджет</label>
            <select
              value={form.budget}
              onChange={(e) => setForm({ ...form, budget: e.target.value })}
            >
              <option value="">Не указано</option>
              <option value="minimum">Бюджет</option>
              <option value="balanced">Баланс</option>
              <option value="premium">Люкс</option>
            </select>
          </div>
          <div className="field">
            <label>Формат ухода</label>
            <select
              value={form.experience}
              onChange={(e) => setForm({ ...form, experience: e.target.value })}
            >
              <option value="">Не указано</option>
              <option value="minimal">Минимально</option>
              <option value="basic">Знаю базовый уход</option>
              <option value="advanced">Продвинутые знания</option>
              <option value="guided">Хочу заботливый шаговый уход</option>
            </select>
          </div>
          <div className="field">
            <label>Задачи ухода через запятую</label>
            <input
              type="text"
              value={form.concerns}
              onChange={(e) => setForm({ ...form, concerns: e.target.value })}
              placeholder="acne, sebum"
            />
          </div>
          <div className="field">
            <label>Приоритеты через запятую</label>
            <input
              type="text"
              value={form.values}
              onChange={(e) => setForm({ ...form, values: e.target.value })}
              placeholder="comfort, price_quality"
            />
          </div>
        </div>

        <div className="accountLinks">
          <button className="btn solid" onClick={save} disabled={saving}>
            {saving ? "Сохраняем…" : "Сохранить профиль"}
          </button>
          <button className="btn ghost" onClick={() => go("history")}>
            История подборов
          </button>
          <button className="btn ghost" onClick={() => go("quiz")}>
            Новый подбор
          </button>
          {user?.role === "admin" ? (
            <button className="btn ghost" onClick={() => go("admin")}>
              Админ-панель
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function HistoryPage({ go, setRecommendation }) {
  const [history, setHistory] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    if (!api.getToken()) return;

    setLoading(true);

    api
      .getMyRecommendations()
      .then((data) => setHistory(data.items || []))
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  }, []);

  const openHistoryItem = (recommendation) => {
    setRecommendation(recommendation);
    go("results");
  };

  return (
    <div className="quizPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <BrandLogo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
        <button className="btn ghost xs" onClick={() => go("account")}>
          кабинет
        </button>
      </header>
      <div className="quizMain wide">
        <h1>История подборов</h1>
        {loading ? <p className="qsub">Обновляем историю…</p> : null}
        <ErrorNote message={error} />

        {history.length ? (
          <div className="histList">
            {history.map((it) => (
              <button
                className="histRow historyButton"
                key={it.recommendation_id}
                onClick={() => openHistoryItem(it)}
              >
                <div>
                  <b>{it.skin_profile?.resolved_skin_type || "Подбор ухода"}</b>
                  <span>
                    {it.created_at ? String(it.created_at).slice(0, 10) : ""}
                  </span>
                  <span>
                    {(it.routine?.morning?.length || 0) +
                      (it.routine?.evening?.length || 0)}{" "}
                    шагов · {it.algorithm_version}
                  </span>
                </div>
                <div style={{ textAlign: "right" }}>
                  <strong>
                    {it.total_price_rub ? it.total_price_rub + " ₽" : ""}
                  </strong>
                  <span>Открыть →</span>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <p className="qsub">Пока нет сохранённых подборов.</p>
        )}

        <button className="btn ghost" onClick={() => go("account")}>
          Назад в кабинет
        </button>
      </div>
    </div>
  );
}

/* ==================== app ==================== */
const PAGES = [
  "home",
  "quiz",
  "review",
  "loading",
  "results",
  "product",
  "feedback",
  "login",
  "register",
  "reset",
  "account",
  "history",
  "admin",
];

function readSessionJson(key, fallback) {
  try {
    const value = sessionStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function App() {
  const [page, setPage] = React.useState(() => {
    const h = window.location.hash.replace("#", "").split("?")[0];
    return PAGES.includes(h) ? h : "home";
  });
  const [questionnaire, setQuestionnaire] = React.useState(null);
  const [questionnaireError, setQuestionnaireError] = React.useState(null);
  const [answers, setAnswers] = React.useState(() =>
    readSessionJson("koyash_quiz_answers", {}),
  );
  const [recommendation, setRecommendation] = React.useState(() =>
    readSessionJson("koyash_latest_recommendation", null),
  );
  const [selectedItem, setSelectedItem] = React.useState(null);
  const [replacementNotice, setReplacementNotice] = React.useState("");
  const [auth, setAuth] = React.useState(null);
  const [authReturnPage, setAuthReturnPage] = React.useState("account");

  const go = (p, { preserveAnswers = false, returnTo = null } = {}) => {
    if (p === "login" || p === "register") {
      setAuthReturnPage(returnTo || "account");
    }
    if (p === "quiz" && !preserveAnswers) {
      setAnswers({});
      setRecommendation(null);
      setSelectedItem(null);
    }
    setPage(p);
    window.location.hash = p;
    window.scrollTo(0, 0);
    if (p === "quiz") {
      api.trackEvent("questionnaire_started", {
        metadata: {
          questionnaire_version: questionnaire?.version || "loading",
        },
      });
    }
  };
  const openItem = (item) => {
    setSelectedItem(item);
    go("product");
  };
  const applyReplacement = (response, product) => {
    const nextRecommendation = recommendation
      ? {
          ...recommendation,
          routine: response.routine,
          total_price_rub: response.total_price_rub,
        }
      : recommendation;
    if (nextRecommendation) {
      try {
        sessionStorage.setItem(
          "koyash_latest_recommendation",
          JSON.stringify(nextRecommendation),
        );
      } catch {
        /* private mode or disabled storage */
      }
    }
    setRecommendation(nextRecommendation);
    setSelectedItem(null);
    setReplacementNotice(
      `${product.name} теперь стоит в подборе вместо прежнего средства. Итоговая сумма пересчитана.`,
    );
    go("results");
  };

  React.useEffect(() => {
    api
      .getQuestionnaire()
      .then(setQuestionnaire)
      .catch((e) => setQuestionnaireError(e.message));
  }, []);

  React.useEffect(() => {
    try {
      sessionStorage.setItem("koyash_quiz_answers", JSON.stringify(answers));
    } catch {
      /* private mode or disabled storage */
    }
  }, [answers]);

  React.useEffect(() => {
    try {
      if (recommendation) {
        sessionStorage.setItem(
          "koyash_latest_recommendation",
          JSON.stringify(recommendation),
        );
      } else {
        sessionStorage.removeItem("koyash_latest_recommendation");
      }
    } catch {
      /* private mode or disabled storage */
    }
  }, [recommendation]);

  React.useEffect(() => {
    if (api.getToken()) {
      api
        .loadAuthState()
        .then(setAuth)
        .catch(() => {
          api.setToken(null);
          setAuth(null);
        });
    }
  }, []);

  React.useEffect(() => {
    const onHash = () => {
      const h = window.location.hash.replace("#", "").split("?")[0];
      if (PAGES.includes(h)) {
        setPage(h);
        return;
      }
      setPage("home");
      window.history.replaceState(null, "", "#home");
    };
    onHash();
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  return (
    <div className="app">
      <div className="pageTransition" key={page} data-page={page}>
        {page === "home" && <Landing go={go} />}
        {page === "quiz" &&
          (questionnaireError ? (
            <CenterInfo
              title="Сервис недоступен"
              text={questionnaireError}
              action={{ label: "На главную", on: () => go("home") }}
            />
          ) : (
            <Quiz
              go={go}
              questionnaire={questionnaire}
              answers={answers}
              setAnswers={setAnswers}
            />
          ))}
        {page === "review" && (
          <Review go={go} questionnaire={questionnaire} answers={answers} />
        )}
        {page === "loading" && (
          <Loading
            go={go}
            answers={answers}
            setAnswers={setAnswers}
            setRecommendation={setRecommendation}
            auth={auth}
            setAuth={setAuth}
          />
        )}
        {page === "results" && (
          <Results
            go={go}
            auth={auth}
            recommendation={recommendation}
            openItem={openItem}
            replacementNotice={replacementNotice}
            clearReplacementNotice={() => setReplacementNotice("")}
          />
        )}
        {page === "product" && (
          <Product
            go={go}
            item={selectedItem}
            recommendation={recommendation}
            onReplacementApplied={applyReplacement}
          />
        )}
        {page === "feedback" && (
          <Feedback
            go={go}
            recommendation={recommendation}
            onReplacementApplied={applyReplacement}
          />
        )}
        {page === "login" && (
          <Login go={go} onAuth={setAuth} returnTo={authReturnPage} />
        )}
        {page === "register" && (
          <Register go={go} onAuth={setAuth} returnTo={authReturnPage} />
        )}
        {page === "reset" && <Reset go={go} />}
        {page === "account" && <Account go={go} auth={auth} setAuth={setAuth} />}
        {page === "history" && (
          <HistoryPage go={go} setRecommendation={setRecommendation} />
        )}
        {page === "admin" && <AdminDashboard go={go} auth={auth} />}
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
