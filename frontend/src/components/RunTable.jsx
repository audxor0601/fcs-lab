import { fmt } from "../format";

/** 앞 회차와 조건이 달라진 지점을 찾는다. */
function conditionChanged(prev, cur) {
  if (!prev || !cur) return false;
  if (prev.posture !== cur.posture) return true;
  if (!prev.target_speed || !cur.target_speed) return false;
  const hi = Math.max(prev.target_speed, cur.target_speed);
  const lo = Math.min(prev.target_speed, cur.target_speed);
  return hi / lo > 1.25;
}

export default function RunTable({ runs, selectedId, onSelect }) {
  return (
    <table>
      <thead>
        <tr>
          <th>회차</th>
          <th>자세</th>
          <th>표적 속도</th>
          <th>명중</th>
          <th>명중률</th>
          <th>명중탄 오차</th>
          <th className="hide-sm">최대</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((r, i) => (
          <tr
            key={r.experiment_id}
            className={[
              r.experiment_id === selectedId ? "on" : "",
              conditionChanged(runs[i - 1], r) ? "divider" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => onSelect(r.experiment_id)}
          >
            <td>
              {r.name}
              {r.note && <span className="row-note">{r.note}</span>}
            </td>
            <td>{r.posture || "—"}</td>
            <td>{r.target_speed === null ? "—" : `${r.target_speed} m/s`}</td>
            <td>
              {r.shots === 0 ? (
                <span className="dash">기록 없음</span>
              ) : (
                `${r.hits}/${r.shots}`
              )}
              {r.unmatched > 0 && (
                <span className="gap">
                  발사 {r.fired} · 미기록 {r.unmatched}
                </span>
              )}
            </td>
            <td className={r.hit_rate === 100 ? "full" : ""}>
              {r.hit_rate === null ? "—" : `${r.hit_rate}%`}
              {!r.hit_rate_reliable && r.shots > 0 && <span className="thin"> *</span>}
              {r.unmatched > 0 && (
                <span className="gap">발사 기준 {r.hit_rate_fired}%</span>
              )}
            </td>
            <td>{fmt(r.median)}</td>
            <td className="hide-sm">{fmt(r.worst)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
