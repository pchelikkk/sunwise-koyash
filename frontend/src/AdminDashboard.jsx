import React from "react";
import {
  Activity,
  ArrowLeft,
  BarChart3,
  Bot,
  Database,
  Eye,
  FileSpreadsheet,
  Image,
  HeartHandshake,
  Pencil,
  RefreshCw,
  Save,
  Share2,
  ShieldCheck,
  ShoppingBag,
  Sparkles,
  UploadCloud,
  UserPlus,
  Users,
  X,
} from "lucide-react";
import * as api from "./api.js";
import BrandLogo from "./BrandLogo.jsx";

const METRICS = [
  {
    key: "registered_total",
    title: "Пользователей",
    icon: Users,
    value: (dashboard) => dashboard.users.registered_total,
    note: (dashboard) => `+${dashboard.users.registered_in_period} за период`,
  },
  {
    key: "unique_visitors",
    title: "Уникальных посетителей",
    icon: Eye,
    value: (dashboard) => dashboard.users.unique_visitors,
    note: (dashboard) => `${dashboard.users.anonymous_visitors} без входа`,
  },
  {
    key: "recommendations_generated",
    title: "Готовых подборов",
    icon: Sparkles,
    value: (dashboard) => dashboard.overview.recommendations_generated,
    note: () => "безопасные рутины",
  },
  {
    key: "questionnaires_completed",
    title: "Заполнено анкет",
    icon: Activity,
    value: (dashboard) => dashboard.overview.questionnaires_completed,
    note: () => "дошли до результата",
  },
  {
    key: "feedback_submitted",
    title: "Получено отзывов",
    icon: HeartHandshake,
    value: (dashboard) => dashboard.overview.feedback_submitted,
    note: () => "по конкретным средствам",
  },
  {
    key: "replacement_sessions",
    title: "Запросов замены",
    icon: RefreshCw,
    value: (dashboard) => dashboard.overview.replacement_sessions,
    note: () => "с вариантами на выбор",
  },
  {
    key: "replacement_selections",
    title: "Принято замен",
    icon: UserPlus,
    value: (dashboard) => dashboard.overview.replacement_selections,
    note: (dashboard) =>
      `${dashboard.conversion.replacement_to_selection.rate_percent}% конверсия`,
  },
  {
    key: "recommendation_shares",
    title: "Поделились подбором",
    icon: Share2,
    value: (dashboard) => dashboard.overview.recommendation_shares,
    note: () => "отправили или скопировали план",
  },
];

const FEEDBACK_LABELS = {
  too_expensive: "Слишком дорого",
  dislikes_brand: "Не нравится бренд",
  composition_concern: "Смущает состав",
  texture_not_suitable: "Не подошла текстура",
  too_many_steps: "Много шагов",
  other: "Другое",
};

const SKIN_TYPE_LABELS = {
  normal: "Нормальная",
  oily: "Жирная",
  dry: "Сухая",
  combination: "Комбинированная",
  sensitive: "Чувствительная",
};

const AUDIENCE_LABELS = {
  ...SKIN_TYPE_LABELS,
  acne: "Высыпания",
  sebum: "Жирный блеск",
  dryness: "Сухость",
  pigmentation: "Пигментация",
  sensitivity: "Чувствительность",
  reactivity: "Реактивность",
  texture: "Неровный рельеф",
  minimum: "До 1 200 ₽",
  balanced: "Средний бюджет",
  premium: "Премиум",
  beginner: "Начинающие",
  basic: "Знают базовый уход",
  guided: "Нужна поддержка",
  advanced: "Опытные",
  minimal: "Минимальный уход",
  custom: "Особые ограничения",
  fragrance: "Отдушки",
  alcohol: "Спирт",
  essential_oils: "Эфирные масла",
};

const CATALOG_ISSUE_LABELS = {
  inactive: "Неактивен",
  missing_ingredients: "Нет состава",
  missing_usage: "Нет инструкции",
  missing_image: "Нет изображения",
  missing_product_link: "Нет ссылки",
};

function rateLabel(value) {
  return value > 100 ? "н/д*" : `${value}%`;
}

function MiniLineChart({ points }) {
  const values = points.map((point) => point.recommendations_generated || 0);
  const max = Math.max(1, ...values);
  const coords = values
    .map((value, index) => {
      const x = values.length <= 1 ? 0 : (index / (values.length - 1)) * 100;
      const y = 82 - (value / max) * 65;
      return `${x},${y}`;
    })
    .join(" ");
  return (
    <svg
      className="lineChart"
      viewBox="0 0 100 90"
      preserveAspectRatio="none"
      aria-label="Динамика подборов"
    >
      <defs>
        <linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ff8db6" stopOpacity=".3" />
          <stop offset="1" stopColor="#ff8db6" stopOpacity="0" />
        </linearGradient>
      </defs>
      <line x1="0" x2="100" y1="82" y2="82" className="chartAxis" />
      {coords ? (
        <polygon points={`0,82 ${coords} 100,82`} fill="url(#chartFill)" />
      ) : null}
      {coords ? (
        <polyline points={coords} fill="none" className="chartLine" />
      ) : null}
    </svg>
  );
}

function RankedBars({ title, items, label }) {
  const max = Math.max(1, ...items.map((item) => item.count));
  return (
    <section className="adminPanel">
      <div className="panelTitle">
        <h2>{title}</h2>
        <BarChart3 size={19} />
      </div>
      <div className="rankedList">
        {items.length ? (
          items.slice(0, 5).map((item, index) => (
            <div
              className="rankedRow"
              key={item.product_external_id || item.value || index}
            >
              <span className="rankNumber">{index + 1}</span>
              <div>
                <b>
                  {label ? label(item) : item.name || item.product_external_id}
                </b>
                <span className="rankBar">
                  <i style={{ width: `${(item.count / max) * 100}%` }} />
                </span>
              </div>
              <strong>{item.count}</strong>
            </div>
          ))
        ) : (
          <p className="muted">За выбранный период данных пока нет.</p>
        )}
      </div>
    </section>
  );
}

function DistributionPanel({ title, values, icon: Icon = BarChart3 }) {
  const items = Object.entries(values || {})
    .map(([value, count]) => ({ value, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6);
  return (
    <section className="adminPanel compactPanel">
      <div className="panelTitle">
        <h2>{title}</h2>
        <Icon size={19} />
      </div>
      <div className="distributionList">
        {items.length ? items.map((item) => (
          <div className="distributionRow" key={item.value}>
            <span>{AUDIENCE_LABELS[item.value] || item.value}</span>
            <b>{item.count}</b>
          </div>
        )) : <p className="muted">Данных за период пока нет.</p>}
      </div>
    </section>
  );
}

function FeedbackProducts({ items }) {
  return (
    <section className="adminPanel feedbackProductsPanel">
      <div className="panelTitle">
        <div>
          <h2>Что именно не подошло</h2>
          <p>Товары с обратной связью и причины — без комментариев и персональных данных</p>
        </div>
        <HeartHandshake size={19} />
      </div>
      <div className="feedbackProductList">
        {items.length ? items.slice(0, 6).map((item) => (
          <div className="feedbackProductRow" key={item.product_external_id}>
            <div>
              <b>{item.name || item.product_external_id}</b>
              <span>{item.brand || "Бренд не указан"}</span>
            </div>
            <div className="feedbackReasonChips">
              {Object.entries(item.reasons).map(([reason, count]) => (
                <span key={reason}>{FEEDBACK_LABELS[reason] || reason} · {count}</span>
              ))}
            </div>
            <strong>{item.count}</strong>
          </div>
        )) : <p className="muted">Негативных отзывов за период нет.</p>}
      </div>
    </section>
  );
}

export default function AdminDashboard({ go, auth }) {
  const [days, setDays] = React.useState(30);
  const [dashboard, setDashboard] = React.useState(null);
  const [quality, setQuality] = React.useState(null);
  const [issues, setIssues] = React.useState(null);
  const [issueFilter, setIssueFilter] = React.useState("all");
  const [editor, setEditor] = React.useState(null);
  const [saving, setSaving] = React.useState(false);
  const [datasetFile, setDatasetFile] = React.useState(null);
  const [synchronizeMissing, setSynchronizeMissing] = React.useState(true);
  const [importing, setImporting] = React.useState(false);
  const [importReport, setImportReport] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  const load = React.useCallback(() => {
    if (!api.getToken() || auth?.user?.role !== "admin") return;
    setLoading(true);
    setError("");
    Promise.all([
      api.getAdminDashboard(days),
      api.getAdminCatalogQuality(),
      api.getAdminCatalogIssues(issueFilter),
    ])
      .then(([analytics, catalog, catalogIssues]) => {
        setDashboard(analytics);
        setQuality(catalog);
        setIssues(catalogIssues);
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  }, [days, auth, issueFilter]);

  React.useEffect(load, [load]);

  if (!api.getToken()) {
    return (
      <div className="centerState">
        <ShieldCheck size={34} />
        <h1>Нужен вход</h1>
        <p>Админ-панель доступна только авторизованным администраторам.</p>
        <button className="button primary" onClick={() => go("login")}>
          Войти
        </button>
      </div>
    );
  }
  if (auth?.user?.role !== "admin") {
    return (
      <div className="centerState">
        <ShieldCheck size={34} />
        <h1>Раздел закрыт</h1>
        <p>У этой учётной записи нет прав администратора.</p>
        <button className="button secondary" onClick={() => go("account")}>
          В кабинет
        </button>
      </div>
    );
  }

  const feedbackItems = dashboard
    ? Object.entries(dashboard.feedback.reasons).map(([value, count]) => ({
        value,
        count,
      }))
    : [];
  const saveEditor = async (event) => {
    event.preventDefault();
    if (!editor) return;
    setSaving(true);
    setError("");
    try {
      await api.updateAdminProduct(editor.external_id, {
        image_url: editor.image_url,
        product_url: editor.product_url,
        how_to_use: editor.how_to_use,
        is_active: editor.is_active,
      });
      setEditor(null);
      load();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  };
  const importDataset = async (event) => {
    event.preventDefault();
    if (!datasetFile || importing) return;
    const form = event.currentTarget;
    setImporting(true);
    setImportReport(null);
    setError("");
    try {
      const report = await api.importAdminCatalogDataset(
        datasetFile,
        synchronizeMissing,
      );
      setImportReport(report);
      setDatasetFile(null);
      form.reset();
      load();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setImporting(false);
    }
  };
  return (
    <main className="adminPage appSurface">
      <header className="innerHeader">
        <BrandLogo onClick={() => go("home")} />
        <div className="adminIdentity">
          <ShieldCheck size={17} /> Защищённая аналитика
        </div>
        <button
          className="button secondary compact"
          onClick={() => go("account")}
        >
          <ArrowLeft size={16} /> Кабинет
        </button>
      </header>
      <section className="adminHero">
        <div>
          <span className="eyebrow">Без персональных данных</span>
          <h1>Пульс продукта</h1>
          <p>
            Доверенные события backend, качество каталога и поведение
            рекомендаций в одном месте.
          </p>
        </div>
        <div className="periodControl">
          {[7, 30, 90].map((value) => (
            <button
              key={value}
              className={days === value ? "active" : ""}
              onClick={() => setDays(value)}
            >
              {value} дней
            </button>
          ))}
          <button onClick={load} aria-label="Обновить">
            <RefreshCw size={17} className={loading ? "spinIcon" : ""} />
          </button>
        </div>
      </section>
      {error ? <div className="notice errorNotice">{error}</div> : null}
      {dashboard ? (
        <>
          <section className="metricGrid">
            {METRICS.map((metric) => {
              const Icon = metric.icon;
              return (
              <article className="metricCard" key={metric.key}>
                <span>
                  <Icon size={19} />
                </span>
                <small>{metric.title}</small>
                <strong>{metric.value(dashboard).toLocaleString("ru-RU")}</strong>
                <em>{metric.note(dashboard)}</em>
              </article>
              );
            })}
          </section>
          <section className="adminGrid wideFirst">
            <article className="adminPanel activityPanel">
              <div className="panelTitle">
                <div>
                  <h2>Динамика подборов</h2>
                  <p>{dashboard.period.calendar_days} календарных дней · UTC</p>
                </div>
                <Activity size={20} />
              </div>
              <MiniLineChart points={dashboard.activity} />
              <div className="chartLegend">
                <span>
                  <i /> Подборы
                </span>
                <b>
                  {dashboard.conversion.questionnaire_to_recommendation
                    .rate_percent > 100
                    ? "История анкеты неполна"
                    : `${dashboard.conversion.questionnaire_to_recommendation.rate_percent}% завершили анкету`}
                </b>
              </div>
            </article>
            <article className="adminPanel conversionPanel">
              <div className="panelTitle">
                <h2>Конверсия</h2>
                <Sparkles size={19} />
              </div>
              {[
                [
                  "Анкета → подбор",
                  dashboard.conversion.questionnaire_to_recommendation
                    .rate_percent,
                ],
                [
                  "Отзыв → замена",
                  dashboard.conversion.feedback_to_replacement.rate_percent,
                ],
                [
                  "Замена → выбор",
                  dashboard.conversion.replacement_to_selection.rate_percent,
                ],
              ].map(([label, value]) => (
                <div className="conversionRow" key={label}>
                  <div>
                    <span>{label}</span>
                    <b>{rateLabel(value)}</b>
                  </div>
                  <span className="progressTrack">
                    <i style={{ width: `${Math.min(100, value)}%` }} />
                  </span>
                </div>
              ))}
              {dashboard.conversion.questionnaire_to_recommendation
                .rate_percent > 100 ? (
                <p className="metricFootnote">
                  * В хранилище есть старые подборы без полного набора
                  funnel-событий.
                </p>
              ) : null}
            </article>
          </section>
          <section className="adminGrid">
            <article className="adminPanel usersPanel">
              <div className="panelTitle">
                <div>
                  <h2>Пользователи</h2>
                  <p>Агрегированные показатели, без имён, почты и идентификаторов</p>
                </div>
                <Users size={20} />
              </div>
              <div className="userFactGrid">
                <span><b>{dashboard.users.registered_total}</b>всего аккаунтов</span>
                <span><b>{dashboard.users.registered_in_period}</b>новых за период</span>
                <span><b>{dashboard.users.active_accounts}</b>активных аккаунтов</span>
                <span><b>{dashboard.users.returning_accounts}</b>вернувшихся</span>
                <span><b>{dashboard.users.unique_visitors}</b>уникальных посетителей</span>
                <span><b>{dashboard.users.anonymous_visitors}</b>гостей без входа</span>
              </div>
            </article>
            <article className="adminPanel llmPanel">
              <div className="panelTitle">
                <div>
                  <h2>LLM-объяснения</h2>
                  <p>{dashboard.llm.provider} · {dashboard.llm.model}</p>
                </div>
                <Bot size={20} />
              </div>
              <div className={`llmStatus ${dashboard.llm.configured ? "ready" : "offline"}`}>
                <span>{dashboard.llm.configured ? "Провайдер подключён" : "Безопасный fallback"}</span>
                <b>{dashboard.llm.success_rate.rate_percent}% успешных</b>
              </div>
              <div className="llmFacts">
                <span><b>{dashboard.llm.attempts}</b>вызовов</span>
                <span><b>{dashboard.llm.success}</b>успешно</span>
                <span><b>{dashboard.llm.fallback}</b>fallback</span>
              </div>
              <p className="metricFootnote llmNote">
                Модель переформулирует только объяснение уже выбранного средства. Фильтры, баллы, состав рутины и ограничения остаются детерминированными.
              </p>
            </article>
          </section>
          <section className="adminGrid fourColumns">
            <RankedBars
              title="Чаще рекомендуют"
              items={dashboard.products.top_recommended}
            />
            <RankedBars
              title="Переходят в магазин"
              items={dashboard.products.top_store_opened}
            />
            <RankedBars
              title="Чаще хотят заменить"
              items={dashboard.products.replacement_frequency}
            />
            <RankedBars
              title="Чаще выбирают на замену"
              items={dashboard.products.replacement_selection_frequency}
            />
          </section>
          <section className="adminGrid">
            <FeedbackProducts items={dashboard.feedback.reasons_by_product} />
            <RankedBars
              title="Причины обратной связи"
              items={feedbackItems}
              label={(item) => FEEDBACK_LABELS[item.value] || item.value}
            />
          </section>
          <section className="adminGrid fourColumns audienceGrid">
            <DistributionPanel title="Типы кожи" values={dashboard.audience.skin_types} icon={Users} />
            <DistributionPanel title="Основные запросы" values={dashboard.audience.concerns} icon={Sparkles} />
            <DistributionPanel title="Бюджеты" values={dashboard.audience.budgets} icon={ShoppingBag} />
            <DistributionPanel title="Опыт в уходе" values={dashboard.audience.experience} icon={BarChart3} />
          </section>
          <section className="adminGrid">
            <article className="adminPanel qualityPanel">
              <div className="panelTitle">
                <div>
                  <h2>Качество каталога</h2>
                  <p>Автоматическая проверка обязательных данных</p>
                </div>
                <Database size={20} />
              </div>
              {quality ? (
                <>
                  <div className="qualityScore">
                    <strong>{quality.completeness_percent}%</strong>
                    <span>заполненность</span>
                  </div>
                  <div className="qualityFacts">
                    <span>
                      <b>{quality.active_products}</b> активных
                    </span>
                    <span>
                      <b>{quality.dataset_products}</b> из датасета
                    </span>
                    <span>
                      <b>{Object.keys(quality.step_counts).length}</b> шагов
                      ухода
                    </span>
                  </div>
                  <div className="coverageList">
                    <span>
                      <i style={{ width: `${quality.usage_coverage_percent}%` }} />
                      <b>Инструкции {quality.usage_coverage_percent}%</b>
                    </span>
                    <span>
                      <i style={{ width: `${quality.product_link_coverage_percent}%` }} />
                      <b>Ссылки {quality.product_link_coverage_percent}%</b>
                    </span>
                    <span>
                      <i style={{ width: `${quality.image_coverage_percent}%` }} />
                      <b>Изображения {quality.image_coverage_percent}%</b>
                    </span>
                  </div>
                  <div
                    className={
                      "qualityStatus " +
                      (quality.strict_dataset_ok ? "good" : "warn")
                    }
                  >
                    <ShieldCheck size={17} />
                    {quality.strict_dataset_ok
                      ? "Каталог соответствует строгому датасет-контракту"
                      : "Есть записи вне основного датасета"}
                  </div>
                </>
              ) : null}
            </article>
            <DistributionPanel
              title="Ограничения и исключения"
              values={dashboard.audience.restrictions}
              icon={ShieldCheck}
            />
          </section>
          <section className="adminPanel datasetImportPanel">
            <div className="panelTitle datasetImportHeading">
              <div>
                <h2>Импорт нового датасета</h2>
                <p>
                  Загрузи CSV или XLSX — сначала проверим все строки и только
                  затем обновим рекомендации. Перезапуск сервиса не нужен.
                </p>
              </div>
              <FileSpreadsheet size={22} />
            </div>
            <form className="datasetImportForm" onSubmit={importDataset}>
              <label className="datasetFilePicker">
                <UploadCloud size={22} />
                <span>
                  <b>{datasetFile ? datasetFile.name : "Выбрать датасет"}</b>
                  <small>
                    {datasetFile
                      ? `${(datasetFile.size / 1024).toFixed(1)} КБ`
                      : "До 10 МБ · заголовки можно писать по-русски"}
                  </small>
                </span>
                <input
                  type="file"
                  accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                  onChange={(event) => {
                    setDatasetFile(event.target.files?.[0] || null);
                    setImportReport(null);
                  }}
                />
              </label>
              <label className="datasetSyncChoice">
                <input
                  type="checkbox"
                  checked={synchronizeMissing}
                  onChange={(event) => setSynchronizeMissing(event.target.checked)}
                />
                <span>
                  <b>Считать файл новым полным каталогом</b>
                  <small>
                    Товары, которых нет в файле, станут неактивными, но останутся
                    в истории и аудите.
                  </small>
                </span>
              </label>
              <button
                className="button primary datasetImportButton"
                disabled={!datasetFile || importing}
              >
                <UploadCloud size={17} />
                {importing ? "Проверяем и импортируем…" : "Проверить и импортировать"}
              </button>
            </form>
            {importReport ? (
              <div className="datasetImportSuccess" role="status">
                <ShieldCheck size={20} />
                <div>
                  <b>Датасет применён без ошибок</b>
                  <span>
                    {importReport.rows_valid} строк · {importReport.inserted} новых ·{" "}
                    {importReport.updated} обновлено · {importReport.deactivated} отключено
                  </span>
                </div>
                <strong>{importReport.active_products_after} активных</strong>
              </div>
            ) : null}
          </section>
          <section className="adminPanel catalogOpsPanel">
            <div className="panelTitle catalogOpsHeading">
              <div>
                <h2>Редактор каталога</h2>
                <p>
                  Точечное обогащение датасета с записью каждого изменения в аудит.
                </p>
              </div>
              <div className="catalogIssueControl">
                <Image size={18} />
                <select
                  value={issueFilter}
                  onChange={(event) => setIssueFilter(event.target.value)}
                >
                  <option value="all">Все проблемы</option>
                  <option value="missing_image">Нет изображения</option>
                  <option value="missing_product_link">Нет ссылки</option>
                  <option value="missing_usage">Нет инструкции</option>
                  <option value="missing_ingredients">Нет состава</option>
                  <option value="inactive">Неактивные</option>
                </select>
              </div>
            </div>
            {issues?.items?.length ? (
              <div className="catalogIssueTable">
                {issues.items.slice(0, 8).map((item) => (
                  <button
                    key={item.external_id}
                    className="catalogIssueRow"
                    onClick={() => setEditor({ ...item })}
                  >
                    <span>
                      <b>{item.name}</b>
                      <small>
                        {item.brand} · {item.external_id}
                      </small>
                    </span>
                    <span className="issueChips">
                      {item.issues.map((issue) => (
                        <i key={issue}>
                          {CATALOG_ISSUE_LABELS[issue] || issue}
                        </i>
                      ))}
                    </span>
                    <Pencil size={17} />
                  </button>
                ))}
                <p className="metricFootnote">
                  Показано {Math.min(8, issues.items.length)} из {issues.total}.
                  Источник и scoring-поля здесь не меняются.
                </p>
              </div>
            ) : (
              <p className="muted">По этому фильтру проблем не найдено.</p>
            )}
          </section>
          {editor ? (
            <div className="adminEditorOverlay" role="dialog" aria-modal="true">
              <button
                className="detailBackdrop"
                onClick={() => setEditor(null)}
                aria-label="Закрыть"
              />
              <form className="adminEditor" onSubmit={saveEditor}>
                <button
                  type="button"
                  className="iconButton editorClose"
                  onClick={() => setEditor(null)}
                  aria-label="Закрыть редактор"
                >
                  <X size={20} />
                </button>
                <span className="eyebrow">{editor.external_id}</span>
                <h2>{editor.name}</h2>
                <label>
                  Изображение
                  <input
                    type="url"
                    placeholder="https://…"
                    value={editor.image_url || ""}
                    onChange={(event) =>
                      setEditor({ ...editor, image_url: event.target.value })
                    }
                  />
                </label>
                <label>
                  Ссылка на продукт
                  <input
                    type="url"
                    placeholder="https://…"
                    value={editor.product_url || ""}
                    onChange={(event) =>
                      setEditor({ ...editor, product_url: event.target.value })
                    }
                  />
                </label>
                <label>
                  Как использовать
                  <textarea
                    rows={4}
                    value={editor.how_to_use || ""}
                    onChange={(event) =>
                      setEditor({ ...editor, how_to_use: event.target.value })
                    }
                  />
                </label>
                <label className="adminActiveCheck">
                  <input
                    type="checkbox"
                    checked={editor.is_active}
                    onChange={(event) =>
                      setEditor({ ...editor, is_active: event.target.checked })
                    }
                  />
                  Использовать в каталоге и рекомендациях
                </label>
                <button className="button primary" disabled={saving}>
                  <Save size={17} /> {saving ? "Сохраняем…" : "Сохранить"}
                </button>
              </form>
            </div>
          ) : null}
        </>
      ) : loading ? (
        <div className="centerState inline">
          <RefreshCw className="spinIcon" />
          <p>Собираем агрегаты…</p>
        </div>
      ) : null}
    </main>
  );
}
