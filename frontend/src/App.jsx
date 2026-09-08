import { useEffect, useState } from "react";
import DispersionChart from "./components/DispersionChart";
import RunDetail from "./components/RunDetail";
import RunTable from "./components/RunTable";
import { useRuns } from "./useRuns";

export default function App() {
  const { runs, loading, error } = useRuns();
  const [selectedId, setSelectedId] = useState(null);

  // 처음 열었을 때 표본이 충분한 회차를 자동으로 편다.
  useEffect(() => {
    if (selectedId || !runs.length) return;
    const first = runs.find((r) => r.reliable) || runs.find((r) => r.n > 0);
    if (first) setSelectedId(first.experiment_id);
  }, [runs, selectedId]);

  if (error) {
    return (
      <div className="wrap">
        <header>
          <h1>사격 실험 기록</h1>
        </header>
        <div className="err">
          서버에 연결하지 못했다. uvicorn 이 켜져 있는지 확인하고 새로고침한다.
          <br />
          <small>{error}</small>
        </div>
      </div>
    );
  }

  const total = runs.reduce((a, r) => a + r.analyzed_shots, 0);
  const solid = runs.filter((r) => r.reliable).length;

  return (
    <div className="wrap">
      <header>
        <h1>사격 실험 기록</h1>
        <p className="state">
          {loading
            ? "불러오는 중"
            : `${runs.length}개 회차, 분석 대상 ${total}발. 표본이 충분한 회차는 ${solid}개.`}
        </p>
      </header>

      {!loading && (
        <>
          <section>
            <h2>회차별 탄착 오차</h2>
            <p className="hint">
              눈금 하나가 한 발이다. 굵은 세로선은 중앙값. 표본이 10발 미만인 회차는 회색으로 두었다.
            </p>
            <DispersionChart runs={runs} />
            <p className="axis-note">지형 오폭(terrain)은 제외했다.</p>
          </section>

          <section>
            <h2>회차 요약</h2>
            <p className="hint">줄을 누르면 아래에 자세히 나온다.</p>
            <RunTable runs={runs} selectedId={selectedId} onSelect={setSelectedId} />
          </section>

          {selectedId && (
            <section>
              <RunDetail id={selectedId} />
            </section>
          )}
        </>
      )}
    </div>
  );
}
