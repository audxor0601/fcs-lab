import { fmt } from "../format";

export default function RunTable({ runs, selectedId, onSelect }) {
  return (
    <table>
      <thead>
        <tr>
          <th>회차</th>
          <th>분석</th>
          <th>중앙값</th>
          <th>평균</th>
          <th className="hide-sm">최소</th>
          <th className="hide-sm">최대</th>
          <th className="hide-sm">표준편차</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((r) => (
          <tr
            key={r.experiment_id}
            className={r.experiment_id === selectedId ? "on" : ""}
            onClick={() => onSelect(r.experiment_id)}
          >
            <td>{r.name}</td>
            <td>
              {r.n === 0 ? (
                <span className="dash">기록 없음</span>
              ) : (
                <span className={r.reliable ? "" : "thin"}>{r.analyzed_shots}발</span>
              )}
            </td>
            <td>{fmt(r.median)}</td>
            <td>{fmt(r.mean)}</td>
            <td className="hide-sm">{fmt(r.best)}</td>
            <td className="hide-sm">{fmt(r.worst)}</td>
            <td className="hide-sm">{fmt(r.stdev)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
