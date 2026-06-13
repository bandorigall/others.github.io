const APP_DATA = window.BANGDREAM_MBTI_DATA;

const STORAGE_KEYS = {
  lang: "bangdream_mbti_lang",
  answers: "bangdream_mbti_answers",
  currentIndex: "bangdream_mbti_current_index",
};

const AXES = [
  ["EI", "E", "I"],
  ["SN", "S", "N"],
  ["FT", "F", "T"],
  ["JP", "J", "P"],
];

const RADAR_ORDER = ["E", "S", "T", "J", "I", "N", "F", "P"];
const BAND_ORDER = ["popipa", "afglo", "pasupare", "roselia", "hhw", "morfo", "ras", "mygo", "ave", "sumimi", "bangdream"];
const MATCH_TUNING = {
  userStretchPower: 0.7,
  characterShrink: 0.85,
  directionWeight: 0.7,
  extremenessWeight: 2.0,
};

const EXPORT_IMAGE_CONFIG = {
  width: 1680,
  height: 1080,
  padding: 76,
  cardGap: 48,
  cardsInset: 24,
  headerHeight: 200,
  sectionGap: 12,
  cardHeight: 752,
};

const LOCAL_ASSET_MAP = window.BANGDREAM_LOCAL_ASSET_MAP || {};
const imageLoadCache = new Map();

const UI = {
  zh: {
    shortLang: "CN",
    htmlLang: "zh-CN",
    title: "BanG Dream! 角色性格拟合度测试",
    heroEyebrow: "Bang Dream Personality Match",
    heroTitle: "测出最像你的 BanG Dream! 角色",
    heroLead: "使用本地 OJTS 三语题库完成 48 道题目，看看你和哪几位 BanG Dream! 角色的八维轮廓最接近。",
    heroCount: "48 道本地题目",
    start: "开始测试",
    retake: "重新测试",
    questionLabel: "测试流程",
    questionTitle: "选择最符合你的选项",
    questionOrder: (index, total) => `第 ${index + 1} / ${total} 题`,
    progressText: (answered, total) => `已作答 ${answered} / ${total}`,
    agreementFormat: "同意度量表",
    bipolarFormat: "双端偏好",
    prev: "上一题",
    next: "下一题",
    resultsLabel: "测试结果",
    resultsTitle: "与你最接近的 3 位角色",
    userResultTitle: "你的八维结果",
    confidence: "结果稳定度",
    confidenceHigh: "高",
    confidenceMedium: "中",
    confidenceLow: "低",
    topPick: "最接近角色",
    matchScore: "拟合度",
    characterType: "角色类型",
    yourType: "你的类型",
    band: "所属",
    chartTitle: "八维雷达图",
    youLegend: "你的结果",
    characterLegend: "角色结果",
    rankLabel: (rank) => `Top ${rank}`,
    saveImage: "打开结果图",
    savingImage: "正在生成...",
    saveFailed: "结果图打开失败，请稍后再试。",
    shareResult: "复制结果链接",
    shareCopied: "链接已复制",
    shareFailed: "复制失败，请手动复制网址。",
    exportTitle: "BanG Dream! 角色性格拟合度测试",
    exportSubtitle: "最接近你的 Top 3 角色",
    exportFilePrefix: "bangdream-mbti-result",
    readmeButton: "Readme",
    readmeClose: "关闭",
    readmeLabel: "Readme",
    readmeTitle: "说明、感谢与免责声明",
    readmeThanksTitle: "参考与鸣谢",
    readmePrivacyTitle: "隐私保护说明",
    readmeDisclaimerTitle: "免责声明",
    readmeThanksIntro: "本页参考与素材来源：",
    privacyBody: "本页面完全在本地浏览器内运行，不会上传答案，不会收集、存储或发送任何用户资料、测试结果或设备信息。",
    disclaimerBody: "本项目代码由 AI 辅助生成，测试结果仅供图一乐和同人向娱乐体验使用，请不要将结果视为专业人格测评或官方角色设定结论。",
    copyright: APP_DATA.meta.copyrightNotice,
    axisMeaning: {
      E: "外向",
      S: "现实",
      T: "理性",
      J: "计划",
      I: "内向",
      N: "直觉",
      F: "情感",
      P: "灵活",
    },
    pairNames: {
      EI: "外向 / 内向",
      SN: "现实 / 直觉",
      FT: "情感 / 理性",
      JP: "计划 / 灵活",
    },
    agreementOptions: [
      ["非常不同意", "几乎完全不符合"],
      ["不同意", "更偏向不符合"],
      ["中立", "说不准 / 看情况"],
      ["同意", "比较符合"],
      ["非常同意", "几乎完全符合"],
    ],
    bipolarOptions: [
      ["更偏左侧", "明显靠近左边"],
      ["稍偏左侧", "有点偏左"],
      ["正中间", "两边都差不多"],
      ["稍偏右侧", "有点偏右"],
      ["更偏右侧", "明显靠近右边"],
    ],
  },
  en: {
    shortLang: "EN",
    htmlLang: "en",
    title: "BanG Dream! Character Match Test",
    heroEyebrow: "Bang Dream Personality Match",
    heroTitle: "Find the BanG Dream! characters closest to you",
    heroLead: "Answer 48 local OJTS questions and compare your eight-dimension profile with BanG Dream! characters.",
    heroCount: "48 local questions",
    start: "Start Test",
    retake: "Retake",
    questionLabel: "Question Flow",
    questionTitle: "Pick the option closest to you",
    questionOrder: (index, total) => `Question ${index + 1} / ${total}`,
    progressText: (answered, total) => `${answered} / ${total} answered`,
    agreementFormat: "Agreement Scale",
    bipolarFormat: "Bipolar Scale",
    prev: "Previous",
    next: "Next",
    resultsLabel: "Results",
    resultsTitle: "Your 3 closest character matches",
    userResultTitle: "Your eight-dimension result",
    confidence: "Result stability",
    confidenceHigh: "High",
    confidenceMedium: "Medium",
    confidenceLow: "Low",
    topPick: "Closest match",
    matchScore: "Match score",
    characterType: "Character type",
    yourType: "Your type",
    band: "Band / Unit",
    chartTitle: "Eight-dimension radar",
    youLegend: "Your result",
    characterLegend: "Character result",
    rankLabel: (rank) => `Top ${rank}`,
    saveImage: "Open Result Image",
    savingImage: "Rendering...",
    saveFailed: "Failed to open the result image. Please try again.",
    shareResult: "Copy Result Link",
    shareCopied: "Link copied",
    shareFailed: "Copy failed. Please copy the URL manually.",
    saveHint: "Long press the image to save it",
    exportTitle: "BanG Dream! Character Match Test",
    exportSubtitle: "Your Top 3 character matches",
    exportFilePrefix: "bangdream-mbti-result",
    readmeButton: "Readme",
    readmeClose: "Close",
    readmeLabel: "Readme",
    readmeTitle: "Notes, Credits, and Disclaimer",
    readmeThanksTitle: "Credits",
    readmePrivacyTitle: "Privacy",
    readmeDisclaimerTitle: "Disclaimer",
    readmeThanksIntro: "This page references the following projects and sources:",
    privacyBody: "This page runs entirely in your local browser. It does not upload answers, and it does not collect, store, or transmit any personal information or test results.",
    disclaimerBody: "The code for this page was generated with AI assistance. The test is meant for fun only and should not be treated as a professional personality assessment or official character canon.",
    copyright: APP_DATA.meta.copyrightNotice,
    axisMeaning: {
      E: "Extraversion",
      S: "Sensing",
      T: "Thinking",
      J: "Judging",
      I: "Introversion",
      N: "Intuition",
      F: "Feeling",
      P: "Perceiving",
    },
    pairNames: {
      EI: "Extraversion / Introversion",
      SN: "Sensing / Intuition",
      FT: "Feeling / Thinking",
      JP: "Judging / Perceiving",
    },
    agreementOptions: [
      ["Strongly disagree", "Almost completely unlike me"],
      ["Disagree", "Leans away from me"],
      ["Neutral", "Depends / not sure"],
      ["Agree", "Feels fairly like me"],
      ["Strongly agree", "Almost completely like me"],
    ],
    bipolarOptions: [
      ["Far left", "Clearly closer to the left side"],
      ["Slightly left", "A bit more left-leaning"],
      ["Middle", "About equally balanced"],
      ["Slightly right", "A bit more right-leaning"],
      ["Far right", "Clearly closer to the right side"],
    ],
  },
  ja: {
    shortLang: "JP",
    htmlLang: "ja",
    title: "BanG Dream! キャラクター適合度テスト",
    heroEyebrow: "Bang Dream Personality Match",
    heroTitle: "あなたに近い BanG Dream! キャラクターを見つける",
    heroLead: "ローカルの OJTS 48 問に答えて、あなたの八次元結果に近い BanG Dream! キャラクターを見つけます。",
    heroCount: "ローカル 48 問",
    start: "テスト開始",
    retake: "もう一度テスト",
    questionLabel: "テスト進行",
    questionTitle: "自分に近い選択肢を選んでください",
    questionOrder: (index, total) => `${index + 1} / ${total} 問`,
    progressText: (answered, total) => `${answered} / ${total} 回答済み`,
    agreementFormat: "同意スケール",
    bipolarFormat: "両極スケール",
    prev: "前へ",
    next: "次へ",
    resultsLabel: "結果",
    resultsTitle: "あなたに近い 3 人のキャラクター",
    userResultTitle: "あなたの八次元結果",
    confidence: "結果の安定度",
    confidenceHigh: "高",
    confidenceMedium: "中",
    confidenceLow: "低",
    topPick: "最も近いキャラ",
    matchScore: "適合度",
    characterType: "キャラタイプ",
    yourType: "あなたのタイプ",
    band: "所属",
    chartTitle: "八次元レーダー",
    youLegend: "あなたの結果",
    characterLegend: "キャラクター結果",
    rankLabel: (rank) => `Top ${rank}`,
    saveImage: "結果画像を開く",
    savingImage: "生成中...",
    saveFailed: "結果画像を開けませんでした。もう一度試してください。",
    shareResult: "結果リンクをコピー",
    shareCopied: "リンクをコピーしました",
    shareFailed: "コピーに失敗しました。URL を手動でコピーしてください。",
    exportTitle: "BanG Dream! キャラクター適合度テスト",
    exportSubtitle: "あなたに近い Top 3 キャラクター",
    exportFilePrefix: "bangdream-mbti-result",
    readmeButton: "Readme",
    readmeClose: "閉じる",
    readmeLabel: "Readme",
    readmeTitle: "説明・謝辞・免責事項",
    readmeThanksTitle: "参考と謝辞",
    readmePrivacyTitle: "プライバシー",
    readmeDisclaimerTitle: "免責事項",
    readmeThanksIntro: "参考にした内容と素材元：",
    privacyBody: "このページは完全にローカルブラウザ内で動作します。回答内容や結果、個人情報を送信・収集・保存することはありません。",
    disclaimerBody: "このページのコードは AI 支援で作成されています。結果はあくまで娯楽向けの参考表示であり、専門的な性格診断や公式設定の断定ではありません。",
    copyright: APP_DATA.meta.copyrightNotice,
    axisMeaning: {
      E: "外向",
      S: "感覚",
      T: "思考",
      J: "判断",
      I: "内向",
      N: "直観",
      F: "感情",
      P: "知覚",
    },
    pairNames: {
      EI: "外向 / 内向",
      SN: "感覚 / 直観",
      FT: "感情 / 思考",
      JP: "判断 / 知覚",
    },
    agreementOptions: [
      ["全くそう思わない", "ほとんど当てはまらない"],
      ["あまりそう思わない", "やや違う"],
      ["どちらでもない", "状況による"],
      ["そう思う", "かなり当てはまる"],
      ["とてもそう思う", "ほぼその通り"],
    ],
    bipolarOptions: [
      ["かなり左寄り", "左側に明確に近い"],
      ["やや左寄り", "少し左に寄る"],
      ["真ん中", "ほぼ半々"],
      ["やや右寄り", "少し右に寄る"],
      ["かなり右寄り", "右側に明確に近い"],
    ],
  },
  ko: {
    shortLang: "KR",
    htmlLang: "ko",
    title: "BanG Dream! 캐릭터 성격 적합도 테스트",
    heroEyebrow: "Bang Dream Personality Match",
    heroTitle: "당신과 가장 닮은 BanG Dream! 캐릭터를 찾아보세요",
    heroLead: "로컬 OJTS 48문항에 답하고, 당신의 8차원 프로필과 가장 가까운 BanG Dream! 캐릭터를 확인해 보세요.",
    heroCount: "로컬 48문항",
    start: "테스트 시작",
    retake: "다시 테스트",
    questionLabel: "테스트 진행",
    questionTitle: "당신에게 가장 잘 맞는 선택지를 고르세요",
    questionOrder: (index, total) => `${index + 1} / ${total} 번`,
    progressText: (answered, total) => `${answered} / ${total} 응답`,
    agreementFormat: "동의 척도",
    bipolarFormat: "양극 척도",
    prev: "이전",
    next: "다음",
    resultsLabel: "테스트 결과",
    resultsTitle: "당신과 가장 가까운 3명의 캐릭터",
    userResultTitle: "당신의 8차원 결과",
    confidence: "결과 안정도",
    confidenceHigh: "높음",
    confidenceMedium: "보통",
    confidenceLow: "낮음",
    topPick: "가장 가까운 캐릭터",
    matchScore: "적합도",
    characterType: "캐릭터 유형",
    yourType: "당신의 유형",
    band: "소속",
    chartTitle: "8차원 레이더 차트",
    youLegend: "당신의 결과",
    characterLegend: "캐릭터 결과",
    rankLabel: (rank) => `Top ${rank}`,
    saveImage: "결과 이미지 열기",
    savingImage: "생성 중...",
    saveFailed: "결과 이미지를 열지 못했습니다. 잠시 후 다시 시도해 주세요.",
    shareResult: "결과 링크 복사",
    shareCopied: "링크가 복사되었습니다",
    shareFailed: "복사에 실패했습니다. 주소를 직접 복사해 주세요.",
    saveHint: "이미지를 길게 눌러 저장하세요",
    exportTitle: "BanG Dream! 캐릭터 성격 적합도 테스트",
    exportSubtitle: "당신과 가장 가까운 Top 3 캐릭터",
    exportFilePrefix: "bangdream-mbti-result",
    readmeButton: "Readme",
    readmeClose: "닫기",
    readmeLabel: "Readme",
    readmeTitle: "설명·감사의 말·면책 조항",
    readmeThanksTitle: "참고 및 감사",
    readmePrivacyTitle: "개인정보 보호",
    readmeDisclaimerTitle: "면책 조항",
    readmeThanksIntro: "이 페이지가 참고한 프로젝트 및 출처:",
    privacyBody: "이 페이지는 전적으로 브라우저 로컬에서 동작합니다. 응답을 업로드하지 않으며, 어떠한 개인정보나 테스트 결과도 수집·저장·전송하지 않습니다.",
    disclaimerBody: "이 페이지의 코드는 AI 보조로 생성되었습니다. 테스트 결과는 재미를 위한 것이며, 전문적인 성격 평가나 공식 캐릭터 설정으로 받아들이지 마세요.",
    copyright: APP_DATA.meta.copyrightNoticeKo || APP_DATA.meta.copyrightNotice,
    axisMeaning: {
      E: "외향",
      S: "감각",
      T: "사고",
      J: "판단",
      I: "내향",
      N: "직관",
      F: "감정",
      P: "인식",
    },
    pairNames: {
      EI: "외향 / 내향",
      SN: "감각 / 직관",
      FT: "감정 / 사고",
      JP: "판단 / 인식",
    },
    agreementOptions: [
      ["전혀 그렇지 않다", "거의 전혀 맞지 않음"],
      ["그렇지 않다", "맞지 않는 편"],
      ["보통", "상황에 따라 다름"],
      ["그렇다", "꽤 잘 맞음"],
      ["매우 그렇다", "거의 완전히 맞음"],
    ],
    bipolarOptions: [
      ["많이 왼쪽", "왼쪽에 뚜렷이 가까움"],
      ["약간 왼쪽", "조금 왼쪽으로 치우침"],
      ["가운데", "양쪽이 거의 비슷함"],
      ["약간 오른쪽", "조금 오른쪽으로 치우침"],
      ["많이 오른쪽", "오른쪽에 뚜렷이 가까움"],
    ],
  },
};

const elements = {
  langSwitcher: document.getElementById("lang-switcher"),
  hero: document.getElementById("hero"),
  quizSection: document.getElementById("quiz-section"),
  resultsSection: document.getElementById("results-section"),
  heroEyebrow: document.getElementById("hero-eyebrow"),
  heroTitle: document.getElementById("hero-title"),
  heroLead: document.getElementById("hero-lead"),
  heroPillCount: document.getElementById("hero-pill-count"),
  startBtn: document.getElementById("start-btn"),
  questionLabel: document.getElementById("question-label"),
  questionTitle: document.getElementById("question-title"),
  progressText: document.getElementById("progress-text"),
  progressFill: document.getElementById("progress-fill"),
  questionOrder: document.getElementById("question-order"),
  questionFormat: document.getElementById("question-format"),
  questionText: document.getElementById("question-text"),
  questionHints: document.getElementById("question-hints"),
  bipolarScale: document.getElementById("bipolar-scale"),
  bipolarLeft: document.getElementById("bipolar-left"),
  bipolarRight: document.getElementById("bipolar-right"),
  answerList: document.getElementById("answer-list"),
  prevBtn: document.getElementById("prev-btn"),
  nextBtn: document.getElementById("next-btn"),
  resultsLabel: document.getElementById("results-label"),
  resultsTitle: document.getElementById("results-title"),
  saveResultBtn: document.getElementById("save-result-btn"),
  shareResultBtn: document.getElementById("share-result-btn"),
  retakeBtnBottom: document.getElementById("retake-btn-bottom"),
  userResult: document.getElementById("user-result"),
  topMatches: document.getElementById("top-matches"),
  readmeBtn: document.getElementById("readme-btn"),
  galleryBtn: document.getElementById("gallery-btn"),
  gallerySection: document.getElementById("gallery-section"),
  galleryLabel: document.getElementById("gallery-label"),
  galleryTitle: document.getElementById("gallery-title"),
  galleryGroups: document.getElementById("gallery-groups"),
  readmeModal: document.getElementById("readme-modal"),
  readmeBackdrop: document.getElementById("readme-backdrop"),
  readmeContent: document.getElementById("readme-content"),
  readmeClose: document.getElementById("readme-close"),
  resultPreviewCard: document.querySelector(".result-preview-card"),
  resultPreviewHeader: document.querySelector(".result-preview-header"),
  resultPreviewModal: document.getElementById("result-preview-modal"),
  resultPreviewBackdrop: document.getElementById("result-preview-backdrop"),
  resultPreviewHint: document.getElementById("result-preview-hint"),
  resultPreviewContent: document.querySelector(".result-preview-content"),
  resultPreviewStage: document.getElementById("result-preview-stage"),
  resultPreviewImage: document.getElementById("result-preview-image"),
  resultPreviewRotate: document.getElementById("result-preview-rotate"),
  resultPreviewCloseIcon: document.getElementById("result-preview-close-icon"),
  resultPreviewClose: document.getElementById("result-preview-close"),
  hoverTooltip: document.getElementById("hover-tooltip"),
  brand: document.querySelector(".brand"),
};

const sharedAnswers = loadAnswersFromURL();

const state = {
  lang: loadLanguage(),
  answers: sharedAnswers || loadAnswers(),
  currentIndex: sharedAnswers ? sharedAnswers.length - 1 : loadCurrentIndex(),
  charts: [],
  view: "home",
  readmeOpen: false,
  resultPreviewOpen: false,
  resultPreviewPortrait: false,
  resultPreviewUrl: "",
  resultPreviewPortraitUrl: "",
  exporting: false,
};

function getQuestions(lang = state.lang) {
  return APP_DATA.questions[lang].questions;
}

function loadLanguage() {
  const saved = localStorage.getItem(STORAGE_KEYS.lang);
  return UI[saved] ? saved : "ko";
}

function loadAnswers() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEYS.answers) || "[]");
    if (Array.isArray(saved) && saved.length === getQuestions("zh").length) {
      return saved.map((value) => (Number.isInteger(value) && value >= 1 && value <= 5 ? value : null));
    }
  } catch (error) {
    console.warn("Failed to read answers", error);
  }
  return Array.from({ length: getQuestions("zh").length }, () => null);
}

const SHARE_PARAM = "a";

function encodeAnswers(answers) {
  return answers.map((value) => (Number.isInteger(value) && value >= 1 && value <= 5 ? String(value) : "0")).join("");
}

function loadAnswersFromURL() {
  try {
    const raw = new URLSearchParams(window.location.search).get(SHARE_PARAM);
    const total = getQuestions("zh").length;
    if (!raw || raw.length !== total || !/^[0-5]+$/.test(raw)) return null;
    const answers = raw.split("").map((ch) => (ch === "0" ? null : Number.parseInt(ch, 10)));
    return answers.some((value) => Number.isInteger(value)) ? answers : null;
  } catch (error) {
    console.warn("Failed to read shared answers", error);
    return null;
  }
}

function buildShareUrl() {
  const url = new URL(window.location.href);
  url.search = "";
  url.hash = "";
  url.searchParams.set(SHARE_PARAM, encodeAnswers(state.answers));
  return url.toString();
}

function loadCurrentIndex() {
  const raw = Number.parseInt(localStorage.getItem(STORAGE_KEYS.currentIndex), 10);
  const total = getQuestions("zh").length;
  return Number.isFinite(raw) ? clamp(raw, 0, total - 1) : 0;
}

function detectInitialView() {
  if (state.answers.every((item) => Number.isInteger(item))) return "results";
  if (state.answers.some((item) => Number.isInteger(item))) return "quiz";
  return "home";
}

function persistState() {
  localStorage.setItem(STORAGE_KEYS.lang, state.lang);
  localStorage.setItem(STORAGE_KEYS.answers, JSON.stringify(state.answers));
  localStorage.setItem(STORAGE_KEYS.currentIndex, String(state.currentIndex));
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function getAnsweredCount() {
  return state.answers.filter((answer) => Number.isInteger(answer)).length;
}

function hasCurrentAnswer() {
  return Number.isInteger(state.answers[state.currentIndex]);
}

function isComplete() {
  return getAnsweredCount() === state.answers.length;
}

function confidenceLabel(confidence) {
  const t = UI[state.lang];
  if (confidence >= 45) return t.confidenceHigh;
  if (confidence >= 22) return t.confidenceMedium;
  return t.confidenceLow;
}

function getSignedAxisValue(percentages, leftPole, rightPole) {
  return (percentages[leftPole] || 0) - (percentages[rightPole] || 0);
}

function getSignedVector(percentages) {
  return AXES.map(([, leftPole, rightPole]) => getSignedAxisValue(percentages, leftPole, rightPole) / 100);
}

function transformUserVector(vector) {
  return vector.map((value) => Math.sign(value) * Math.pow(Math.abs(value), MATCH_TUNING.userStretchPower));
}

function transformCharacterVector(vector) {
  return vector.map((value) => value * MATCH_TUNING.characterShrink);
}

function getVectorNorm(vector) {
  return Math.sqrt(vector.reduce((sum, value) => sum + value * value, 0));
}

function getCosineSimilarity(left, right) {
  const leftNorm = getVectorNorm(left);
  const rightNorm = getVectorNorm(right);
  if (!leftNorm || !rightNorm) return 0;
  const dot = left.reduce((sum, value, index) => sum + value * right[index], 0);
  return clamp(dot / (leftNorm * rightNorm), -1, 1);
}

function getWeightedAxisCloseness(userVector, characterVector) {
  const weighted = userVector.reduce(
    (acc, value, index) => {
      const characterValue = characterVector[index];
      const weight = 1 + Math.max(Math.abs(value), Math.abs(characterValue)) * MATCH_TUNING.extremenessWeight;
      const closeness = clamp(1 - Math.abs(value - characterValue) / 2, 0, 1);
      acc.score += closeness * weight;
      acc.weight += weight;
      return acc;
    },
    { score: 0, weight: 0 }
  );

  return weighted.weight ? weighted.score / weighted.weight : 0;
}

function computeUserResult() {
  if (!isComplete()) return null;
  const scores = { E: 0, I: 0, S: 0, N: 0, F: 0, T: 0, J: 0, P: 0 };
  const questions = getQuestions("en");

  questions.forEach((question, index) => {
    const answer = state.answers[index];
    if (!Number.isInteger(answer)) return;
    if (question.format === "agreement") {
      const support = answer - 1;
      question.poles.forEach((pole) => {
        scores[pole] += support;
      });
    } else {
      scores[question.left_pole] += 5 - answer;
      scores[question.right_pole] += answer - 1;
    }
  });

  const percentages = {};
  const pairMargins = {};
  const type = [];

  AXES.forEach(([axis, left, right]) => {
    const total = scores[left] + scores[right];
    const leftPct = total ? clamp(Math.round((scores[left] / total) * 10000) / 100, 1, 99) : 50;
    const rightPct = Math.round((100 - leftPct) * 100) / 100;
    const winner = leftPct >= rightPct ? left : right;
    percentages[left] = leftPct;
    percentages[right] = rightPct;
    pairMargins[axis] = {
      winner,
      loser: winner === left ? right : left,
      margin: Math.round(Math.abs(leftPct - rightPct) * 100) / 100,
    };
    type.push(winner);
  });

  const confidence = Math.round(
    (Object.values(pairMargins).reduce((sum, item) => sum + item.margin, 0) / AXES.length) * 100
  ) / 100;

  return {
    scores,
    percentages,
    pairMargins,
    confidence,
    type: type.join(""),
  };
}

function computeMatches(userPercentages) {
  const userVector = transformUserVector(getSignedVector(userPercentages));

  return APP_DATA.characters
    .map((character) => {
      const characterVector = transformCharacterVector(getSignedVector(character.percentages));
      const directionScore = (getCosineSimilarity(userVector, characterVector) + 1) / 2;
      const axisCloseness = getWeightedAxisCloseness(userVector, characterVector);
      const compositeScore =
        directionScore * MATCH_TUNING.directionWeight +
        axisCloseness * (1 - MATCH_TUNING.directionWeight);
      const similarity = Math.round(clamp(compositeScore, 0, 1) * 10000) / 100;

      return {
        ...character,
        similarity: clamp(similarity, 0, 100),
        matchScore: compositeScore,
        directionScore,
        axisCloseness,
      };
    })
    .sort(
      (a, b) =>
        b.matchScore - a.matchScore ||
        b.directionScore - a.directionScore ||
        b.axisCloseness - a.axisCloseness ||
        a.id.localeCompare(b.id)
    );
}

function getLocalizedCharacterName(character, lang = state.lang) {
  return character.names?.[lang] || character.fullName || character.englishName || character.displayName || "";
}

function getLocalizedCharacterDescription(character, lang = state.lang) {
  return character.descriptions?.[lang] || character.description || "";
}

function getSecondaryCharacterNames(character, lang = state.lang) {
  const primary = getLocalizedCharacterName(character, lang);
  const seen = new Set([primary]);
  return ["ko", "zh", "en", "ja"]
    .filter((item) => item !== lang)
    .map((item) => character.names?.[item])
    .filter((name) => name && !seen.has(name) && seen.add(name));
}

function getLocalizedBandName(character, lang = state.lang) {
  if (character.bandKey === "bangdream") {
    if (lang === "ko") return "기타 캐릭터";
    if (lang === "zh") return "其他角色";
    if (lang === "ja") return "その他キャラクター";
    return "Other Characters";
  }
  return character.bandName;
}

function createElement(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function getEmbeddedAssetMap() {
  return window.BANGDREAM_EMBEDDED_ASSET_MAP || {};
}

function resolveAssetUrl(url) {
  const localUrl = LOCAL_ASSET_MAP[url] || url;
  const embeddedAssetMap = getEmbeddedAssetMap();
  return embeddedAssetMap[url] || embeddedAssetMap[localUrl] || localUrl;
}

function normalizeAssetUrl(url) {
  const resolvedUrl = resolveAssetUrl(url);
  try {
    return new URL(resolvedUrl, window.location.href).href;
  } catch {
    return resolvedUrl;
  }
}

function waitForImageElement(image, cacheKey) {
  return new Promise((resolve, reject) => {
    const cleanup = () => {
      image.removeEventListener("load", handleLoad);
      image.removeEventListener("error", handleError);
    };

    const handleLoad = () => {
      cleanup();
      imageLoadCache.set(cacheKey, Promise.resolve(image));
      resolve(image);
    };

    const handleError = () => {
      cleanup();
      imageLoadCache.delete(cacheKey);
      reject(new Error(`Failed to load image: ${image.currentSrc || image.src || cacheKey}`));
    };

    if (image.complete) {
      if (image.naturalWidth > 0) {
        handleLoad();
      } else {
        handleError();
      }
      return;
    }

    image.addEventListener("load", handleLoad, { once: true });
    image.addEventListener("error", handleError, { once: true });
  });
}

function setAssetImageSource(image, url) {
  const cacheKey = normalizeAssetUrl(url);
  image.decoding = "async";
  image.dataset.assetKey = cacheKey;
  image.src = resolveAssetUrl(url);

  if (image.complete && image.naturalWidth > 0) {
    imageLoadCache.set(cacheKey, Promise.resolve(image));
    return;
  }

  if (!imageLoadCache.has(cacheKey)) {
    imageLoadCache.set(cacheKey, waitForImageElement(image, cacheKey));
  }
}

function loadExportImage(url) {
  const cacheKey = normalizeAssetUrl(url);
  const cachedImage = imageLoadCache.get(cacheKey);
  if (cachedImage) {
    return cachedImage.catch(() => {
      imageLoadCache.delete(cacheKey);
      return loadExportImage(url);
    });
  }

  const resolvedUrl = resolveAssetUrl(url);
  const loadingPromise = new Promise((resolve, reject) => {
    const image = new Image();
    if (/^https?:/i.test(resolvedUrl)) image.crossOrigin = "anonymous";
    image.decoding = "async";
    image.onload = () => {
      imageLoadCache.set(cacheKey, Promise.resolve(image));
      resolve(image);
    };
    image.onerror = () => {
      imageLoadCache.delete(cacheKey);
      reject(new Error(`Failed to load image: ${resolvedUrl}`));
    };
    image.src = resolvedUrl;
  });

  imageLoadCache.set(cacheKey, loadingPromise);
  return loadingPromise;
}

function canvasToBlob(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob);
      else reject(new Error("Canvas export failed"));
    }, "image/png");
  });
}

function isMobileLikeDevice() {
  const coarsePointer = window.matchMedia ? window.matchMedia("(pointer: coarse)").matches : false;
  return coarsePointer || /Android|webOS|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent || "");
}

function isRestrictedInAppBrowser() {
  const ua = navigator.userAgent || "";
  return /MicroMessenger|QQ\//i.test(ua);
}

function nextPaint() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve());
  });
}

function cleanupResultPreviewUrl() {
  if (!state.resultPreviewUrl) return;
  URL.revokeObjectURL(state.resultPreviewUrl);
  state.resultPreviewUrl = "";
}

function cleanupResultPreviewPortraitUrl() {
  if (!state.resultPreviewPortraitUrl) return;
  URL.revokeObjectURL(state.resultPreviewPortraitUrl);
  state.resultPreviewPortraitUrl = "";
}

function getViewportMetrics() {
  const viewport = window.visualViewport;
  const width = Math.round(viewport?.width || window.innerWidth || document.documentElement.clientWidth || 0);
  const height = Math.round(viewport?.height || window.innerHeight || document.documentElement.clientHeight || 0);
  return { width, height };
}

function resetResultPreviewLayout() {
  elements.resultPreviewStage.style.removeProperty("height");
  elements.resultPreviewStage.style.removeProperty("minHeight");
  elements.resultPreviewStage.style.removeProperty("width");
  elements.resultPreviewImage.style.removeProperty("width");
  elements.resultPreviewImage.style.removeProperty("height");
}

function getPreviewStageBounds() {
  const contentRect = elements.resultPreviewContent.getBoundingClientRect();
  const width = Math.max(0, Math.floor(contentRect.width));
  const height = Math.max(0, Math.floor(contentRect.height));
  return { width, height };
}

function updateResultPreviewLayout() {
  elements.resultPreviewCard?.classList.toggle("is-portrait", state.resultPreviewPortrait);
  elements.resultPreviewStage.classList.toggle("is-portrait", state.resultPreviewPortrait);

  if (!state.resultPreviewOpen) {
    resetResultPreviewLayout();
    return;
  }

  const { width: viewportWidth, height: viewportHeight } = getViewportMetrics();
  const isMobile = isMobileLikeDevice();
  const headerHeight = Math.ceil(elements.resultPreviewHeader?.getBoundingClientRect().height || 52);
  const stageHeight = state.resultPreviewPortrait && isMobile
    ? Math.max(0, viewportHeight - headerHeight)
    : Math.max(0, viewportHeight - headerHeight - 32);
  elements.resultPreviewStage.style.width = "100%";
  elements.resultPreviewStage.style.height = `${stageHeight}px`;
  elements.resultPreviewStage.style.minHeight = `${stageHeight}px`;

  const { width: stageWidth, height: stageBoundsHeight } = getPreviewStageBounds();
  const sourceWidth = elements.resultPreviewImage.naturalWidth || (state.resultPreviewPortrait ? EXPORT_IMAGE_CONFIG.height : EXPORT_IMAGE_CONFIG.width);
  const sourceHeight = elements.resultPreviewImage.naturalHeight || (state.resultPreviewPortrait ? EXPORT_IMAGE_CONFIG.width : EXPORT_IMAGE_CONFIG.height);
  const scale = Math.min(stageWidth / sourceWidth, stageBoundsHeight / sourceHeight);
  const imageWidth = Math.max(1, Math.floor(sourceWidth * scale));
  const imageHeight = Math.max(1, Math.floor(sourceHeight * scale));

  elements.resultPreviewImage.style.width = `${imageWidth}px`;
  elements.resultPreviewImage.style.height = `${imageHeight}px`;

  console.info("Result preview viewport", {
    viewportWidth,
    viewportHeight,
    sourceWidth,
    sourceHeight,
    stageWidth,
    stageHeight: stageBoundsHeight,
    imageWidth,
    imageHeight,
    portrait: state.resultPreviewPortrait,
  });
}

function loadImageElement(url) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.decoding = "async";
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error(`Failed to load preview image: ${url}`));
    image.src = url;
  });
}

async function ensurePortraitPreviewUrl() {
  if (state.resultPreviewPortraitUrl) return state.resultPreviewPortraitUrl;
  if (!state.resultPreviewUrl) return "";

  const image = await loadImageElement(state.resultPreviewUrl);
  const canvas = document.createElement("canvas");
  canvas.width = image.naturalHeight;
  canvas.height = image.naturalWidth;
  const ctx = canvas.getContext("2d");
  ctx.translate(canvas.width / 2, canvas.height / 2);
  ctx.rotate(Math.PI / 2);
  ctx.drawImage(image, -image.naturalWidth / 2, -image.naturalHeight / 2);
  const rotatedBlob = await canvasToBlob(canvas);
  state.resultPreviewPortraitUrl = URL.createObjectURL(rotatedBlob);
  return state.resultPreviewPortraitUrl;
}

async function syncResultPreviewImage() {
  const nextUrl = state.resultPreviewPortrait
    ? await ensurePortraitPreviewUrl()
    : state.resultPreviewUrl;
  if (!nextUrl) return;
  if (elements.resultPreviewImage.src !== nextUrl) {
    elements.resultPreviewImage.src = nextUrl;
  }
}

function closeResultPreview() {
  state.resultPreviewOpen = false;
  state.resultPreviewPortrait = false;
  elements.resultPreviewModal.hidden = true;
  elements.resultPreviewCard?.classList.remove("is-portrait");
  elements.resultPreviewStage.classList.remove("is-portrait");
  elements.resultPreviewImage.removeAttribute("src");
  elements.resultPreviewHint.textContent = "";
  resetResultPreviewLayout();
  cleanupResultPreviewUrl();
  cleanupResultPreviewPortraitUrl();
}

function getResultPreviewHintText() {
  if (isMobileLikeDevice()) {
    return state.lang === "ko"
      ? "가로 보기와 세로 보기를 전환할 수 있습니다"
      : state.lang === "zh"
      ? "可切换横屏或竖屏查看"
      : state.lang === "ja"
        ? "横向き表示と縦向き表示を切り替えて見られます"
        : "Switch between landscape and portrait viewing";
  }

  return "";
}

function getResultPreviewRotateText() {
  return state.resultPreviewPortrait
    ? (state.lang === "ko" ? "가로 보기" : state.lang === "zh" ? "切回横屏" : state.lang === "ja" ? "横向き表示" : "Landscape View")
    : (state.lang === "ko" ? "세로 보기" : state.lang === "zh" ? "切换竖屏" : state.lang === "ja" ? "縦向き表示" : "Portrait View");
}

function showResultPreview(blob) {
  cleanupResultPreviewPortraitUrl();
  cleanupResultPreviewUrl();
  state.resultPreviewUrl = URL.createObjectURL(blob);
  state.resultPreviewOpen = true;
  state.resultPreviewPortrait = false;
  elements.resultPreviewCard?.classList.remove("is-portrait");
  elements.resultPreviewStage.classList.remove("is-portrait");
  elements.resultPreviewHint.textContent = getResultPreviewHintText();
  elements.resultPreviewRotate.textContent = getResultPreviewRotateText();
  elements.resultPreviewRotate.hidden = !isMobileLikeDevice();
  elements.resultPreviewClose.textContent = UI[state.lang].readmeClose;
  elements.resultPreviewImage.src = state.resultPreviewUrl;
  elements.resultPreviewModal.hidden = false;
}

function openBlobPreview(blob, fileName, previewWindow = null) {
  showResultPreview(blob);
}

function refreshResultPreviewLayoutSoon() {
  requestAnimationFrame(() => updateResultPreviewLayout());
}

function addRoundedRectPath(ctx, x, y, width, height, radius) {
  const safeRadius = Math.min(radius, width / 2, height / 2);
  ctx.beginPath();
  ctx.moveTo(x + safeRadius, y);
  ctx.lineTo(x + width - safeRadius, y);
  ctx.arcTo(x + width, y, x + width, y + safeRadius, safeRadius);
  ctx.lineTo(x + width, y + height - safeRadius);
  ctx.arcTo(x + width, y + height, x + width - safeRadius, y + height, safeRadius);
  ctx.lineTo(x + safeRadius, y + height);
  ctx.arcTo(x, y + height, x, y + height - safeRadius, safeRadius);
  ctx.lineTo(x, y + safeRadius);
  ctx.arcTo(x, y, x + safeRadius, y, safeRadius);
  ctx.closePath();
}

function fillRoundedRect(ctx, x, y, width, height, radius, fillStyle) {
  addRoundedRectPath(ctx, x, y, width, height, radius);
  ctx.fillStyle = fillStyle;
  ctx.fill();
}

function strokeRoundedRect(ctx, x, y, width, height, radius, strokeStyle, lineWidth = 1) {
  addRoundedRectPath(ctx, x, y, width, height, radius);
  ctx.strokeStyle = strokeStyle;
  ctx.lineWidth = lineWidth;
  ctx.stroke();
}

function moveHoverTooltip(clientX, clientY) {
  const tooltip = elements.hoverTooltip;
  if (tooltip.hidden) return;

  const offset = 14;
  const rect = tooltip.getBoundingClientRect();
  const maxLeft = window.innerWidth - rect.width - 12;
  const maxTop = window.innerHeight - rect.height - 12;
  const left = Math.min(clientX + offset, Math.max(12, maxLeft));
  const top = Math.min(clientY + offset, Math.max(12, maxTop));

  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
}

function showHoverTooltip(text, clientX, clientY) {
  if (!text) return;
  elements.hoverTooltip.textContent = text;
  elements.hoverTooltip.hidden = false;
  moveHoverTooltip(clientX, clientY);
}

function hideHoverTooltip() {
  elements.hoverTooltip.hidden = true;
}

function attachHoverTooltip(node, text) {
  node.addEventListener("mouseenter", (event) => {
    showHoverTooltip(text, event.clientX, event.clientY);
  });
  node.addEventListener("mousemove", (event) => {
    moveHoverTooltip(event.clientX, event.clientY);
  });
  node.addEventListener("mouseleave", hideHoverTooltip);
}

function getGalleryButtonText() {
  return state.lang === "ko" ? "캐릭터 도감" : state.lang === "zh" ? "角色图鉴" : state.lang === "ja" ? "キャラ一覧" : "Characters";
}

function getGalleryLabelText() {
  return state.lang === "ko" ? "캐릭터 도감" : state.lang === "zh" ? "角色图鉴" : state.lang === "ja" ? "キャラ一覧" : "Character Gallery";
}

function getGalleryTitleText() {
  return state.lang === "ko"
    ? "밴드별로 전체 캐릭터 보기"
    : state.lang === "zh"
    ? "按乐队查看全部角色"
    : state.lang === "ja"
      ? "バンド別に全キャラクターを見る"
      : "Browse Every Character by Band";
}

function getCharacterCountText(count) {
  return state.lang === "ko"
    ? `${count}명`
    : state.lang === "zh"
    ? `${count} 位角色`
    : state.lang === "ja"
      ? `${count} 人`
      : `${count} characters`;
}

function renderLanguageSwitcher() {
  elements.langSwitcher.innerHTML = "";
  Object.entries(UI).forEach(([lang, meta]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = meta.shortLang;
    button.className = lang === state.lang ? "is-active" : "";
    button.addEventListener("click", () => {
      state.lang = lang;
      persistState();
      render();
    });
    elements.langSwitcher.appendChild(button);
  });
}

function renderHero() {
  const t = UI[state.lang];
  document.documentElement.lang = t.htmlLang;
  document.title = t.title;
  elements.heroEyebrow.textContent = t.heroEyebrow;
  elements.heroTitle.textContent = t.heroTitle;
  elements.heroLead.textContent = t.heroLead;
  elements.heroPillCount.textContent = t.heroCount;
  elements.startBtn.textContent = t.start;
  elements.galleryBtn.textContent = getGalleryButtonText();
}

function renderQuestion() {
  const t = UI[state.lang];
  const questions = getQuestions(state.lang);
  const question = questions[state.currentIndex];
  const answer = state.answers[state.currentIndex];
  const questionLabelText =
    state.lang === "ko" ? "응답 진행" :
    state.lang === "zh" ? "答题流程" :
    state.lang === "ja" ? "回答フロー" :
    "Answer Flow";

  elements.questionLabel.textContent = questionLabelText;
  elements.questionTitle.textContent = t.questionTitle;
  elements.progressText.textContent = t.progressText(getAnsweredCount(), questions.length);
  elements.progressFill.style.width = `${(getAnsweredCount() / questions.length) * 100}%`;
  elements.questionOrder.textContent = t.questionOrder(state.currentIndex, questions.length);
  elements.questionFormat.textContent = question.format === "agreement" ? t.agreementFormat : t.bipolarFormat;
  elements.questionText.textContent = question.format === "agreement" ? question.text : `${question.left_text} <-> ${question.right_text}`;

  elements.questionHints.innerHTML = "";
  elements.questionHints.hidden = true;

  if (question.format === "bipolar") {
    elements.bipolarScale.hidden = false;
    elements.bipolarLeft.textContent = question.left_text;
    elements.bipolarRight.textContent = question.right_text;
  } else {
    elements.bipolarScale.hidden = true;
  }

  const options = question.format === "agreement"
    ? t.agreementOptions.map(([title, subtitle], index) => ({ title, subtitle, value: index + 1 })).reverse()
    : t.bipolarOptions.map(([title, subtitle], index) => ({ title, subtitle, value: index + 1 }));
  elements.answerList.className = question.format === "bipolar" ? "answer-list is-bipolar" : "answer-list";
  elements.answerList.innerHTML = "";

  options.forEach(({ title, subtitle, value }) => {
    const button = createElement("button", `answer-btn${question.format === "bipolar" ? " is-bipolar" : ""}`);
    button.type = "button";
    if (answer === value) button.classList.add("is-selected");
    button.append(createElement("strong", null, title), createElement("span", null, subtitle));
    button.addEventListener("click", () => {
      state.answers[state.currentIndex] = value;
      persistState();
      render();
      window.clearTimeout(button._advanceTimer);
      button._advanceTimer = window.setTimeout(() => {
        if (state.currentIndex < state.answers.length - 1) {
          state.currentIndex += 1;
          persistState();
          render();
        } else if (isComplete()) {
          showResults();
        }
      }, 120);
    });
    elements.answerList.appendChild(button);
  });

  elements.prevBtn.textContent = t.prev;
  elements.nextBtn.textContent = t.next;
  elements.prevBtn.disabled = state.currentIndex === 0;
  elements.nextBtn.disabled = state.currentIndex === state.answers.length - 1 || !hasCurrentAnswer();
}

function renderUserResult(userResult, matches) {
  const t = UI[state.lang];
  elements.resultsLabel.textContent = t.resultsLabel;
  elements.resultsTitle.textContent = t.resultsTitle;
  elements.saveResultBtn.textContent = state.exporting ? t.savingImage : t.saveImage;
  elements.saveResultBtn.disabled = !userResult || state.exporting;
  if (!state.shareJustCopied) elements.shareResultBtn.textContent = t.shareResult;
  elements.shareResultBtn.disabled = !userResult;
  elements.retakeBtnBottom.textContent = t.retake;

  if (!userResult) {
    elements.userResult.innerHTML = "";
    elements.topMatches.innerHTML = "";
    state.charts = [];
    return;
  }

  elements.userResult.innerHTML = "";
  const head = createElement("div", "user-result-head");
  const left = document.createElement("div");
  left.append(
    createElement("p", "section-label", t.userResultTitle),
    createElement("h3", "result-type", userResult.type)
  );

  const right = createElement("div", "result-summary");
  right.append(
    createElement("span", "stat-chip", `${t.confidence}: ${confidenceLabel(userResult.confidence)} (${userResult.confidence.toFixed(1)})`),
    createElement("span", "stat-chip", `${t.topPick}: ${getLocalizedCharacterName(matches[0])}`),
    createElement("span", "stat-chip", `${t.matchScore}: ${matches[0].similarity.toFixed(2)}%`)
  );
  head.append(left, right);
  elements.userResult.appendChild(head);

  const axisBars = createElement("div", "axis-bars");
  AXES.forEach(([axis, leftPole, rightPole]) => {
    const wrapper = createElement("div", "axis-bar");
    const header = document.createElement("header");
    header.append(
      createElement("span", null, t.pairNames[axis]),
      createElement("strong", null, `${userResult.percentages[leftPole].toFixed(2)} / ${userResult.percentages[rightPole].toFixed(2)}`)
    );
    const track = createElement("div", "bar-track");
    const fill = createElement("div", "bar-fill");
    fill.style.width = `${userResult.percentages[leftPole]}%`;
    track.appendChild(fill);
    wrapper.append(header, track);
    axisBars.appendChild(wrapper);
  });
  elements.userResult.appendChild(axisBars);
}

function renderMatchCards(userResult, matches) {
  const t = UI[state.lang];
  elements.topMatches.innerHTML = "";

  matches.slice(0, 3).forEach((character, index) => {
    const localizedName = getLocalizedCharacterName(character);
    const secondaryNames = getSecondaryCharacterNames(character);
    const localizedDescription = getLocalizedCharacterDescription(character);
    const localizedBandName = getLocalizedBandName(character);
    const card = createElement("article", "match-card");
    card.style.setProperty("--card-color", character.color);

    const visual = createElement("div", "match-visual");
    visual.appendChild(createElement("span", "rank-badge", t.rankLabel(index + 1)));
    const portrait = document.createElement("img");
    portrait.className = "portrait";
    portrait.alt = localizedName;
    setAssetImageSource(portrait, character.portraitUrl);
    visual.appendChild(portrait);

    const body = createElement("div", "match-body");
    const topline = createElement("div", "match-topline");
    const titleWrap = document.createElement("div");
    titleWrap.append(
      createElement("h3", "match-name", localizedName),
      createElement("div", "match-sub", `${character.englishName} · ${t.characterType}: ${character.type}`)
    );
    topline.append(titleWrap, createElement("span", "fit-chip", `${t.matchScore}: ${character.similarity.toFixed(2)}%`));
    titleWrap.querySelector(".match-name").textContent = localizedName;
    titleWrap.querySelector(".match-sub").textContent = `${secondaryNames.join(" / ")}${secondaryNames.length ? " · " : ""}${t.characterType}: ${character.type}`;

    titleWrap.querySelector(".match-sub").textContent = `${secondaryNames.join(" / ")}${secondaryNames.length ? " / " : ""}${t.characterType}: ${character.type}`;

    const bands = createElement("div", "match-bands");
    const bandChip = createElement("div", "band-chip");
    bandChip.title = `${t.band}: ${localizedBandName}`;
    const logo = document.createElement("img");
    logo.alt = localizedBandName;
    setAssetImageSource(logo, character.bandLogoUrl);
    bandChip.append(logo, createElement("span", null, localizedBandName));
    bands.appendChild(bandChip);

    const stats = createElement("div", "match-stats");
    stats.append(
      createElement("span", "stat-chip", `${t.yourType}: ${userResult.type}`),
      createElement("span", "stat-chip", `${t.characterType}: ${character.type}`),
      createElement("span", "stat-chip", `${t.band}: ${localizedBandName}`)
    );

    const description = createElement("p", "result-description", localizedDescription);
    const chartCard = createElement("div", "chart-card");
    chartCard.appendChild(createElement("div", "mini-label", t.chartTitle));
    const legend = createElement("div", "chart-legend");
    const userLegend = document.createElement("span");
    userLegend.innerHTML = `<span class="legend-swatch" style="background:#7b7b7b;"></span> ${t.youLegend}`;
    const charLegend = document.createElement("span");
    charLegend.innerHTML = `<span class="legend-swatch" style="background:${character.color};"></span> ${t.characterLegend}`;
    legend.append(userLegend, charLegend);
    chartCard.appendChild(legend);
    const canvas = document.createElement("canvas");
    canvas.className = "radar-canvas";
    chartCard.appendChild(canvas);
    state.charts.push({ canvas, userPercentages: userResult.percentages, character });

    body.append(topline, bands, stats, description, chartCard);
    card.append(visual, body);
    elements.topMatches.appendChild(card);
  });

  rerenderCharts();
}

function renderGallery() {
  const t = UI[state.lang];
  elements.galleryLabel.textContent = getGalleryLabelText();
  elements.galleryTitle.textContent = getGalleryTitleText();
  elements.galleryGroups.innerHTML = "";

  BAND_ORDER.forEach((bandKey) => {
    const characters = APP_DATA.characters
      .filter((character) => character.bandKey === bandKey)
      .sort((a, b) => getLocalizedCharacterName(a).localeCompare(getLocalizedCharacterName(b), UI[state.lang].htmlLang));

    if (!characters.length) return;
    const localizedBandName = getLocalizedBandName(characters[0]);

    const group = createElement("section", "gallery-group");
    const header = createElement("div", "gallery-group-head");
    const titleWrap = document.createElement("div");
    const bandTitle = createElement("h3", "gallery-band-title", localizedBandName);
    const meta = createElement("span", "gallery-band-count", getCharacterCountText(characters.length));
    titleWrap.append(bandTitle);

    const chip = createElement("div", "band-chip");
    chip.title = localizedBandName;
    const logo = document.createElement("img");
    logo.alt = localizedBandName;
    setAssetImageSource(logo, characters[0].bandLogoUrl);
    chip.append(logo, createElement("span", null, localizedBandName));

    header.append(titleWrap, createElement("div", "gallery-band-meta"));
    header.lastChild.append(meta, chip);

    const grid = createElement("div", "gallery-grid");

    characters.forEach((character) => {
      const localizedName = getLocalizedCharacterName(character);
      const secondaryNames = getSecondaryCharacterNames(character);
      const localizedBandNameForCard = getLocalizedBandName(character);
      const card = createElement("article", "gallery-item");
      card.style.setProperty("--card-color", character.color);

      const visual = createElement("div", "gallery-visual");
      const portrait = document.createElement("img");
      portrait.alt = localizedName;
      setAssetImageSource(portrait, character.portraitUrl);
      visual.appendChild(portrait);

      const body = createElement("div", "gallery-body");
      body.append(
        createElement("h4", "gallery-name", localizedName),
        createElement("div", "gallery-sub", secondaryNames.join(" / ")),
      );

      const metaRow = createElement("div", "gallery-meta");
      metaRow.append(
        createElement("span", "stat-chip", `${UI[state.lang].characterType}: ${character.type}`),
        createElement("span", "stat-chip", localizedBandNameForCard),
      );

      const description = createElement("p", "gallery-description", getLocalizedCharacterDescription(character));
      attachHoverTooltip(description, getLocalizedCharacterDescription(character));
      const chartCard = createElement("div", "chart-card gallery-chart-card");
      chartCard.appendChild(createElement("div", "mini-label", t.chartTitle));
      const canvas = document.createElement("canvas");
      canvas.className = "radar-canvas gallery-radar-canvas";
      canvas.dataset.minSize = "180";
      canvas.dataset.maxSize = "240";
      chartCard.appendChild(canvas);
      state.charts.push({ canvas, character });

      body.append(metaRow, description, chartCard);

      card.append(visual, body);
      grid.appendChild(card);
    });

    group.append(header, grid);
    elements.galleryGroups.appendChild(group);
  });
}

function drawRadar(canvas, userPercentages, character) {
  const t = UI[state.lang];
  const labels = RADAR_ORDER.map((pole) => t.axisMeaning[pole]);
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const minSize = Number.parseFloat(canvas.dataset.minSize || "260");
  const maxSize = Number.parseFloat(canvas.dataset.maxSize || "420");
  const size = Math.max(minSize, Math.min(rect.width || maxSize, maxSize));
  canvas.width = size * dpr;
  canvas.height = size * dpr;

  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, size, size);

  const center = size / 2;
  const radius = size * 0.31;
  ctx.strokeStyle = "rgba(105, 79, 55, 0.12)";
  ctx.lineWidth = 1;

  for (let ring = 1; ring <= 5; ring += 1) {
    ctx.beginPath();
    RADAR_ORDER.forEach((_, index) => {
      const point = getRadarPoint(index, ring / 5, center, radius);
      if (index === 0) ctx.moveTo(point.x, point.y);
      else ctx.lineTo(point.x, point.y);
    });
    ctx.closePath();
    ctx.stroke();
  }

  RADAR_ORDER.forEach((_, index) => {
    const outer = getRadarPoint(index, 1, center, radius);
    ctx.beginPath();
    ctx.moveTo(center, center);
    ctx.lineTo(outer.x, outer.y);
    ctx.stroke();
  });

  drawPolygon(ctx, center, radius, character.percentages, hexToRgba(character.color, 0.95), hexToRgba(character.color, 0.2));
  if (userPercentages) {
    drawPolygon(ctx, center, radius, userPercentages, "rgba(115, 115, 115, 0.96)", "rgba(115, 115, 115, 0.18)");
  }

  ctx.fillStyle = "rgba(57, 43, 31, 0.88)";
  ctx.font = `${size < 220 ? 9 : size < 320 ? 11 : 12}px sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  labels.forEach((label, index) => {
    const point = getRadarPoint(index, 1.15, center, radius);
    ctx.fillText(label, point.x, point.y);
  });
}

function drawPolygon(ctx, center, radius, percentages, stroke, fill) {
  ctx.beginPath();
  RADAR_ORDER.forEach((pole, index) => {
    const point = getRadarPoint(index, percentages[pole] / 100, center, radius);
    if (index === 0) ctx.moveTo(point.x, point.y);
    else ctx.lineTo(point.x, point.y);
  });
  ctx.closePath();
  ctx.fillStyle = fill;
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 2.5;
  ctx.fill();
  ctx.stroke();
}

function getRadarPoint(index, ratio, center, radius) {
  const angle = (-Math.PI / 2) + (Math.PI * 2 * index) / RADAR_ORDER.length;
  return {
    x: center + Math.cos(angle) * radius * ratio,
    y: center + Math.sin(angle) * radius * ratio,
  };
}

function hexToRgba(hex, alpha) {
  const normalized = hex.replace("#", "");
  const r = Number.parseInt(normalized.slice(0, 2), 16);
  const g = Number.parseInt(normalized.slice(2, 4), 16);
  const b = Number.parseInt(normalized.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function formatPercent(value) {
  return `${value.toFixed(2)}%`;
}

function fitText(ctx, text, maxWidth) {
  if (!text) return "";
  if (ctx.measureText(text).width <= maxWidth) return text;
  let fitted = text;
  while (fitted.length > 1 && ctx.measureText(`${fitted}...`).width > maxWidth) {
    fitted = fitted.slice(0, -1);
  }
  return `${fitted}...`;
}

function drawContainImage(ctx, image, x, y, width, height, options = {}) {
  if (!image) return;

  const { alignY = "center" } = options;
  const naturalWidth = image.naturalWidth || image.videoWidth || image.width;
  const naturalHeight = image.naturalHeight || image.videoHeight || image.height;
  if (!naturalWidth || !naturalHeight) return;
  const scale = Math.min(width / naturalWidth, height / naturalHeight);
  const drawWidth = naturalWidth * scale;
  const drawHeight = naturalHeight * scale;
  const drawX = x + (width - drawWidth) / 2;
  const drawY =
    alignY === "bottom"
      ? y + height - drawHeight
      : alignY === "top"
        ? y
        : y + (height - drawHeight) / 2;

  ctx.drawImage(image, drawX, drawY, drawWidth, drawHeight);
}

function drawExportPill(ctx, options) {
  const {
    x,
    y,
    text,
    fill = "rgba(255, 255, 255, 0.9)",
    color = "#2d2219",
    font = "600 18px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif",
    paddingX = 14,
    height = 36,
    radius = 18,
    width = null,
    fit = false,
  } = options;

  ctx.save();
  ctx.font = font;
  const pillWidth = width ?? Math.ceil(ctx.measureText(text).width + paddingX * 2);
  const renderText = fit ? fitText(ctx, text, pillWidth - paddingX * 2) : text;
  fillRoundedRect(ctx, x, y, pillWidth, height, radius, fill);
  ctx.fillStyle = color;
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  ctx.fillText(renderText, x + paddingX, y + height / 2 + 1);
  ctx.restore();
  return pillWidth;
}

async function loadOptionalExportImage(url) {
  try {
    return await loadExportImage(url);
  } catch (error) {
    console.warn(error);
    return null;
  }
}

async function buildExportAssets(matches) {
  return Promise.all(
    matches.map(async (character) => ({
      character,
      portrait: await loadOptionalExportImage(character.portraitUrl),
      bandLogo: await loadOptionalExportImage(character.bandLogoUrl),
    }))
  );
}

function drawExportBackground(ctx, width, height) {
  ctx.fillStyle = "#fff8ef";
  ctx.fillRect(0, 0, width, height);

  const warmGlow = ctx.createRadialGradient(240, 120, 40, 240, 120, 420);
  warmGlow.addColorStop(0, "rgba(255, 149, 102, 0.28)");
  warmGlow.addColorStop(1, "rgba(255, 149, 102, 0)");
  ctx.fillStyle = warmGlow;
  ctx.fillRect(0, 0, width, height);

  const coolGlow = ctx.createRadialGradient(width - 220, 200, 50, width - 220, 200, 420);
  coolGlow.addColorStop(0, "rgba(46, 177, 171, 0.18)");
  coolGlow.addColorStop(1, "rgba(46, 177, 171, 0)");
  ctx.fillStyle = coolGlow;
  ctx.fillRect(0, 0, width, height);

  ctx.save();
  ctx.strokeStyle = "rgba(181, 135, 92, 0.08)";
  ctx.lineWidth = 1;
  for (let x = 40; x < width; x += 120) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
  }
  for (let y = 36; y < height; y += 120) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
  ctx.restore();
}

function drawExportHeader(ctx, userResult, matches, width) {
  const t = UI[state.lang];
  const { padding, headerHeight } = EXPORT_IMAGE_CONFIG;
  const panelY = padding;
  const panelHeight = headerHeight;
  const panelWidth = width - padding * 2;
  const summaryWidth = 372;
  const summaryX = padding + panelWidth - summaryWidth - 18;
  const summaryY = panelY + 16;
  const summaryHeight = panelHeight - 32;

  fillRoundedRect(ctx, padding, panelY, panelWidth, panelHeight, 28, "rgba(255, 252, 247, 0.92)");
  strokeRoundedRect(ctx, padding, panelY, panelWidth, panelHeight, 28, "rgba(136, 102, 70, 0.12)");

  ctx.save();
  ctx.fillStyle = "#2d2219";
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.font = "800 38px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif";
  ctx.fillText(t.exportTitle, padding + 28, panelY + 24);
  ctx.fillStyle = "#6e5948";
  ctx.font = "500 21px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif";
  ctx.fillText(t.exportSubtitle, padding + 28, panelY + 72);
  ctx.fillStyle = "#9b513d";
  ctx.font = "700 15px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif";
  ctx.fillText(t.yourType, padding + 28, panelY + 118);
  ctx.fillStyle = "#2d2219";
  ctx.font = "800 58px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif";
  ctx.fillText(userResult.type, padding + 28, panelY + 132);
  ctx.restore();

  fillRoundedRect(ctx, summaryX, summaryY, summaryWidth, summaryHeight, 24, "rgba(255, 255, 255, 0.95)");
  strokeRoundedRect(ctx, summaryX, summaryY, summaryWidth, summaryHeight, 24, "rgba(136, 102, 70, 0.1)");

  drawExportPill(ctx, {
    x: summaryX + 22,
    y: summaryY + 18,
    text: `${t.confidence}: ${confidenceLabel(userResult.confidence)} ${userResult.confidence.toFixed(1)}`,
    fill: "rgba(255, 245, 237, 1)",
    color: "#9b513d",
    font: "700 17px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif",
    width: summaryWidth - 44,
    height: 40,
    fit: true,
  });

  drawExportPill(ctx, {
    x: summaryX + 22,
    y: summaryY + 66,
    text: `${t.topPick}: ${getLocalizedCharacterName(matches[0])}`,
    fill: "rgba(242, 251, 249, 1)",
    color: "#2f8078",
    font: "700 17px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif",
    width: summaryWidth - 44,
    height: 40,
    fit: true,
  });

  drawExportPill(ctx, {
    x: summaryX + 22,
    y: summaryY + 114,
    text: `${t.matchScore}: ${matches[0].similarity.toFixed(2)}%`,
    fill: "rgba(255, 255, 255, 1)",
    color: "#6e5948",
    font: "700 17px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif",
    width: summaryWidth - 44,
    height: 40,
    fit: true,
  });
}

function drawExportMatchCard(ctx, asset, userResult, rank, x, y, width, height) {
  const t = UI[state.lang];
  const { character, portrait, bandLogo } = asset;
  const localizedName = getLocalizedCharacterName(character);
  const secondaryNames = getSecondaryCharacterNames(character).join(" / ");
  const localizedBandName = getLocalizedBandName(character);
  const cardPadding = 20;

  fillRoundedRect(ctx, x, y, width, height, 28, "rgba(255, 252, 247, 0.95)");
  strokeRoundedRect(ctx, x, y, width, height, 28, "rgba(136, 102, 70, 0.12)");
  fillRoundedRect(ctx, x, y + 12, 8, height - 24, 8, character.color);

  drawExportPill(ctx, {
    x: x + cardPadding,
    y: y + cardPadding,
    text: t.rankLabel(rank),
    fill: "rgba(39, 28, 19, 0.82)",
    color: "#ffffff",
    font: "700 18px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif",
  });

  const scoreText = `${t.matchScore}: ${formatPercent(character.similarity)}`;
  ctx.save();
  ctx.font = "700 18px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif";
  const scoreWidth = Math.ceil(ctx.measureText(scoreText).width + 28);
  ctx.restore();
  drawExportPill(ctx, {
    x: x + width - cardPadding - scoreWidth,
    y: y + cardPadding,
    text: scoreText,
    fill: hexToRgba(character.color, 0.16),
    color: character.color,
    font: "700 18px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif",
  });

  ctx.save();
  ctx.fillStyle = "#2d2219";
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.font = "800 30px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif";
  ctx.fillText(fitText(ctx, localizedName, width - cardPadding * 2), x + cardPadding, y + 74);

  ctx.fillStyle = "#6e5948";
  ctx.font = "500 15px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif";
  if (secondaryNames) {
    ctx.fillText(fitText(ctx, secondaryNames, width - cardPadding * 2), x + cardPadding, y + 112);
  }
  ctx.restore();

  drawExportPill(ctx, {
    x: x + cardPadding,
    y: y + 150,
    text: `${t.characterType}: ${character.type}`,
    fill: "rgba(255, 255, 255, 0.92)",
    color: "#6e5948",
    font: "600 15px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif",
    width: width - cardPadding * 2,
    height: 34,
    paddingX: 12,
    fit: true,
  });

  drawExportPill(ctx, {
    x: x + cardPadding,
    y: y + 192,
    text: `${t.band}: ${localizedBandName}`,
    fill: "rgba(255, 255, 255, 0.92)",
    color: "#6e5948",
    font: "600 15px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif",
    width: width - cardPadding * 2,
    height: 34,
    paddingX: 12,
    fit: true,
  });

  const visualX = x + cardPadding;
  const visualY = y + 238;
  const visualWidth = width - cardPadding * 2;
  const visualHeight = 238;
  fillRoundedRect(ctx, visualX, visualY, visualWidth, visualHeight, 22, hexToRgba(character.color, 0.08));
  strokeRoundedRect(ctx, visualX, visualY, visualWidth, visualHeight, 22, "rgba(136, 102, 70, 0.08)");

  ctx.save();
  addRoundedRectPath(ctx, visualX, visualY, visualWidth, visualHeight, 22);
  ctx.clip();
  if (portrait) {
    drawContainImage(ctx, portrait, visualX - 24, visualY + 6, visualWidth + 48, visualHeight - 6, { alignY: "bottom" });
  }
  ctx.restore();

  if (bandLogo) {
    const logoWidth = 120;
    const logoHeight = 42;
    fillRoundedRect(ctx, visualX + visualWidth - logoWidth - 14, visualY + 14, logoWidth, logoHeight, 16, "rgba(255, 255, 255, 0.94)");
    drawContainImage(ctx, bandLogo, visualX + visualWidth - logoWidth - 8, visualY + 18, logoWidth - 12, logoHeight - 8);
  }

  const chartWrapX = x + cardPadding;
  const chartWrapY = y + 494;
  const chartWrapWidth = width - cardPadding * 2;
  const chartWrapHeight = height - (chartWrapY - y) - cardPadding;
  fillRoundedRect(ctx, chartWrapX, chartWrapY, chartWrapWidth, chartWrapHeight, 22, "rgba(255, 255, 255, 0.82)");
  strokeRoundedRect(ctx, chartWrapX, chartWrapY, chartWrapWidth, chartWrapHeight, 22, "rgba(136, 102, 70, 0.08)");

  ctx.save();
  ctx.fillStyle = "#6e5948";
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.font = "700 16px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif";
  ctx.fillText(t.chartTitle, chartWrapX + 16, chartWrapY + 14);
  ctx.restore();

  const userLegendWidth = drawExportPill(ctx, {
    x: chartWrapX + 16,
    y: chartWrapY + 42,
    text: t.youLegend,
    fill: "rgba(115, 115, 115, 0.12)",
    color: "#666666",
    font: "600 14px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif",
    height: 30,
    paddingX: 12,
    radius: 15,
  });

  drawExportPill(ctx, {
    x: chartWrapX + 28 + userLegendWidth,
    y: chartWrapY + 42,
    text: t.characterLegend,
    fill: hexToRgba(character.color, 0.14),
    color: character.color,
    font: "600 14px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif",
    height: 30,
    paddingX: 12,
    radius: 15,
  });

  const radarCanvas = document.createElement("canvas");
  radarCanvas.dataset.minSize = "184";
  radarCanvas.dataset.maxSize = "184";
  drawRadar(radarCanvas, userResult.percentages, character);
  const radarSize = 184;
  const radarX = chartWrapX + (chartWrapWidth - radarSize) / 2;
  const radarY = chartWrapY + 72;
  ctx.drawImage(radarCanvas, radarX, radarY, radarSize, radarSize);
}

async function buildResultImageCanvas(userResult, matches) {
  if (document.fonts?.ready) {
    await document.fonts.ready.catch(() => undefined);
  }

  const assets = await buildExportAssets(matches.slice(0, 3));
  const canvas = document.createElement("canvas");
  canvas.width = EXPORT_IMAGE_CONFIG.width;
  canvas.height = EXPORT_IMAGE_CONFIG.height;
  const ctx = canvas.getContext("2d");

  drawExportBackground(ctx, canvas.width, canvas.height);
  drawExportHeader(ctx, userResult, matches, canvas.width);

  const { padding, cardGap, cardsInset, headerHeight, sectionGap, cardHeight } = EXPORT_IMAGE_CONFIG;
  const cardsY = padding + headerHeight + sectionGap;
  const cardsStartX = padding + cardsInset;
  const cardsTotalWidth = canvas.width - padding * 2 - cardsInset * 2;
  const cardWidth = (cardsTotalWidth - cardGap * 2) / 3;

  assets.forEach((asset, index) => {
    const cardX = cardsStartX + index * (cardWidth + cardGap);
    drawExportMatchCard(ctx, asset, userResult, index + 1, cardX, cardsY, cardWidth, cardHeight);
  });

  ctx.save();
  ctx.fillStyle = "rgba(110, 89, 72, 0.9)";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.font = "500 17px Outfit, 'Noto Sans SC', 'Noto Sans JP', sans-serif";
  ctx.fillText(fitText(ctx, APP_DATA.meta.copyrightNotice, canvas.width - 120), canvas.width / 2, canvas.height - 28);
  ctx.restore();

  return canvas;
}

function getExportFileName(userResult) {
  const t = UI[state.lang];
  const date = new Date();
  const stamp = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  return `${t.exportFilePrefix}-${userResult.type.toLowerCase()}-${stamp}.png`;
}

async function saveResultImage(previewWindow = null) {
  const userResult = computeUserResult();
  if (!userResult || state.exporting) return;

  const matches = computeMatches(userResult.percentages);
  const t = UI[state.lang];
  state.exporting = true;
  renderUserResult(userResult, matches);

  try {
    await nextPaint();
    const canvas = await buildResultImageCanvas(userResult, matches);
    const blob = await canvasToBlob(canvas);
    openBlobPreview(blob, getExportFileName(userResult), previewWindow);
  } catch (error) {
    console.error("Failed to export result image", error);
    if (previewWindow && !previewWindow.closed) {
      previewWindow.close();
    }
    window.alert(t.saveFailed);
  } finally {
    state.exporting = false;
    renderUserResult(userResult, matches);
  }
}

function rerenderCharts() {
  state.charts.forEach(({ canvas, userPercentages = null, character }) => {
    drawRadar(canvas, userPercentages, character);
  });
}

function renderReadme() {
  const t = UI[state.lang];
  elements.readmeBtn.textContent = t.readmeButton;
  elements.readmeClose.textContent = t.readmeClose;
  elements.readmeContent.innerHTML = `
    <section class="readme-block">
      <h3>${t.readmeDisclaimerTitle}</h3>
      <p>${t.disclaimerBody}</p>
    </section>
    <section class="readme-block">
      <h3>${t.readmePrivacyTitle}</h3>
      <p>${t.privacyBody}</p>
    </section>
    <section class="readme-block">
      <h3>${t.readmeThanksTitle}</h3>
      <p>${t.readmeThanksIntro}</p>
      <ul class="readme-link-list">
        <li><a href="https://github.com/bitterndumpling/bangdream_mbti" target="_blank" rel="noreferrer">원작 — bitterndumpling/bangdream_mbti</a></li>
        <li><a href="${APP_DATA.meta.referenceSite}" target="_blank" rel="noreferrer">jcver.github.io/Gakumas-idolmaster-MBTI-test</a></li>
        <li><a href="${APP_DATA.meta.ojtsSource}" target="_blank" rel="noreferrer">OpenPsychometrics OJTS v2.1</a></li>
        <li><a href="${APP_DATA.meta.fandomWiki}" target="_blank" rel="noreferrer">BanG Dream! Wikia</a></li>
        <li><a href="https://www.personality-database.com" target="_blank" rel="noreferrer">Personality Database</a></li>
        <li><a href="https://bestdori.com" target="_blank" rel="noreferrer">Bestdori!</a></li>
      </ul>
      <p class="copyright-note">${t.copyright}</p>
    </section>
  `;
  elements.readmeModal.hidden = !state.readmeOpen;
  elements.resultPreviewHint.textContent = getResultPreviewHintText();
  elements.resultPreviewRotate.textContent = getResultPreviewRotateText();
  elements.resultPreviewRotate.hidden = !isMobileLikeDevice();
  elements.resultPreviewClose.textContent = t.readmeClose;
  elements.resultPreviewModal.hidden = !state.resultPreviewOpen;
  refreshResultPreviewLayoutSoon();
}

function renderView(userResult) {
  if (state.view === "results" && !userResult) {
    state.view = getAnsweredCount() > 0 ? "quiz" : "home";
  }
  elements.hero.hidden = state.view !== "home";
  elements.quizSection.hidden = state.view !== "quiz";
  elements.resultsSection.hidden = state.view !== "results" || !userResult;
  elements.gallerySection.hidden = state.view !== "gallery";
}

function render() {
  const userResult = computeUserResult();
  const matches = userResult ? computeMatches(userResult.percentages) : [];
  state.charts = [];
  renderLanguageSwitcher();
  renderHero();
  renderQuestion();
  renderUserResult(userResult, matches);
  if (userResult) renderMatchCards(userResult, matches);
  if (state.view === "gallery") renderGallery();
  renderReadme();
  renderView(userResult);
  rerenderCharts();
}

function showQuiz() {
  state.view = "quiz";
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showResults() {
  if (!isComplete()) return;
  state.view = "results";
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetQuiz() {
  state.answers = Array.from({ length: state.answers.length }, () => null);
  state.currentIndex = 0;
  state.view = "home";
  persistState();
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showGallery() {
  state.view = "gallery";
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

elements.startBtn.addEventListener("click", showQuiz);
elements.galleryBtn.addEventListener("click", showGallery);
elements.saveResultBtn.addEventListener("click", () => {
  saveResultImage();
});
elements.shareResultBtn.addEventListener("click", shareResultLink);
elements.retakeBtnBottom.addEventListener("click", resetQuiz);

async function copyTextToClipboard(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch (error) {
    /* fall through to legacy path */
  }
  try {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(textarea);
    return ok;
  } catch (error) {
    return false;
  }
}

async function shareResultLink() {
  if (!isComplete()) return;
  const t = UI[state.lang];
  const url = buildShareUrl();
  const ok = await copyTextToClipboard(url);
  state.shareJustCopied = true;
  elements.shareResultBtn.textContent = ok ? t.shareCopied : t.shareFailed;
  window.clearTimeout(state.shareResetTimer);
  state.shareResetTimer = window.setTimeout(() => {
    state.shareJustCopied = false;
    elements.shareResultBtn.textContent = t.shareResult;
  }, 2000);
}
elements.prevBtn.addEventListener("click", () => {
  state.currentIndex = clamp(state.currentIndex - 1, 0, state.answers.length - 1);
  persistState();
  render();
});
elements.nextBtn.addEventListener("click", () => {
  if (!hasCurrentAnswer()) return;
  state.currentIndex = clamp(state.currentIndex + 1, 0, state.answers.length - 1);
  persistState();
  render();
});
elements.readmeBtn.addEventListener("click", () => {
  state.readmeOpen = true;
  renderReadme();
});
elements.readmeClose.addEventListener("click", () => {
  state.readmeOpen = false;
  renderReadme();
});
elements.readmeBackdrop.addEventListener("click", () => {
  state.readmeOpen = false;
  renderReadme();
});
elements.resultPreviewRotate.addEventListener("click", async () => {
  state.resultPreviewPortrait = !state.resultPreviewPortrait;
  elements.resultPreviewRotate.textContent = getResultPreviewRotateText();
  await syncResultPreviewImage();
  refreshResultPreviewLayoutSoon();
});
elements.resultPreviewCloseIcon.addEventListener("click", closeResultPreview);
elements.resultPreviewClose.addEventListener("click", closeResultPreview);
elements.resultPreviewBackdrop.addEventListener("click", closeResultPreview);
elements.brand.addEventListener("click", (event) => {
  event.preventDefault();
  state.view = "home";
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && state.readmeOpen) {
    state.readmeOpen = false;
    renderReadme();
  }
  if (event.key === "Escape" && state.resultPreviewOpen) {
    closeResultPreview();
  }
  if (event.key === "Escape" && !elements.hoverTooltip.hidden) {
    hideHoverTooltip();
  }
});

elements.resultPreviewImage.addEventListener("load", refreshResultPreviewLayoutSoon);

window.addEventListener("resize", debounce(() => {
  rerenderCharts();
  refreshResultPreviewLayoutSoon();
}, 100));
window.addEventListener("scroll", hideHoverTooltip, { passive: true });

function debounce(fn, delay) {
  let timer = null;
  return (...args) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => fn(...args), delay);
  };
}

if (sharedAnswers) {
  persistState();
  try {
    const cleanUrl = new URL(window.location.href);
    cleanUrl.searchParams.delete(SHARE_PARAM);
    window.history.replaceState(null, "", cleanUrl.pathname + cleanUrl.search + cleanUrl.hash);
  } catch (error) {
    /* ignore URL cleanup failures */
  }
}

state.view = detectInitialView();
render();
