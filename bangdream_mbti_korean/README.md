# BanG Dream! MBTI 캐릭터 적합도 테스트 (한국어판)

OJTS(Open Jungian Type Scales) 문항을 기반으로, 당신의 성격과 가장 닮은 BanG Dream! 캐릭터를 찾아 주는 비공식 팬 제작 성격 테스트입니다.

원작(중국어판)을 한국어로 번역·이식한 버전이며, **순수 비영리 팬 콘텐츠**입니다.

## 사용 방법

`site/` 폴더가 그 자체로 완성된 정적 사이트입니다. 별도 빌드 과정이 필요 없습니다.

```bash
# 로컬에서 바로 실행
python -m http.server -d site 8000
# → 브라우저에서 http://localhost:8000
```

GitHub Pages에 올릴 때는 `site/` 폴더의 내용을 배포 루트에 두면 됩니다.

48개 문항에 답하면 8차원(EI/SN/FT/JP) 프로필이 계산되고, 49명의 캐릭터 중 가장 가까운 Top 3을 보여 줍니다. 한국어·中文·English·日本語를 지원합니다.

## 원작 및 출처

본 프로젝트는 아래 자료를 참고·이식했습니다.

- 원작(중국어판): [bitterndumpling/bangdream_mbti](https://github.com/bitterndumpling/bangdream_mbti) · 샘플 사이트 [bangdream-mbti.cn](http://www.bangdream-mbti.cn/)
- 한국어판 이식·번역: [bandorigall/others.github.io](https://github.com/bandorigall/others.github.io)
- 원작이 참고한 프로젝트: [jcver.github.io/Gakumas-idolmaster-MBTI-test](https://jcver.github.io/Gakumas-idolmaster-MBTI-test/)
- 문항: [OpenPsychometrics OJTS v2.1](https://openpsychometrics.org/tests/OJTS/) — **CC BY-NC-SA 4.0**
- 캐릭터 자료: [BanG Dream! Wikia](https://bandori.fandom.com/), [Bestdori!](https://bestdori.com), [Personality Database](https://www.personality-database.com)

## 라이선스 및 저작권 안내

- 문항(OJTS v2.1)은 **CC BY-NC-SA 4.0** 라이선스를 따릅니다. 따라서 본 한국어 번역본 역시 **비영리 + 출처 표시 + 동일 조건 변경 허락** 조건을 그대로 준수합니다.
- 본 페이지에 사용된 BanG Dream! 관련 명칭·이미지·캐릭터 등 모든 소재의 저작권은 **Bushiroad**에 있으며, 비상업적 팬 창작 용도로만 사용됩니다.
- **본 프로젝트는 어떠한 형태의 수익화(광고·후원·유료화 등)도 하지 않습니다.**
- 권리자의 요청이 있을 경우 즉시 게시를 중단합니다.

## 면책 조항

- 코드 일부는 AI 보조로 생성되었습니다.
- 테스트 결과는 오락·동인 목적의 재미를 위한 것이며, 전문적인 성격 평가나 공식 캐릭터 설정으로 받아들이지 마세요.
- 모든 처리는 브라우저 로컬에서 이루어지며, 응답이나 결과를 수집·저장·전송하지 않습니다.
