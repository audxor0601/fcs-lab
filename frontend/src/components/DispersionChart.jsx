import { useEffect, useRef, useState } from "react";

/**
 * 회차별 탄착 분포.
 * 막대 하나로 평균만 보여주면 오폭 몇 발에 속는다.
 * 개별 탄착을 전부 찍고 중앙값만 굵게 표시한다.
 */
export default function DispersionChart({ runs }) {
  const boxRef = useRef(null);
  const [width, setWidth] = useState(800);

  useEffect(() => {
    const measure = () => {
      if (boxRef.current) setWidth(boxRef.current.clientWidth);
    };
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, []);

  const usable = runs.filter((r) => r.n > 0);
  if (!usable.length) return null;

  const rowH = 26;
  const padL = 46;
  const padR = 16;
  const padT = 8;
  const padB = 26;
  const height = padT + usable.length * rowH + padB;
  const max = Math.max(...usable.map((r) => r.worst)) * 1.05;
  const x = (v) => padL + (v / max) * (width - padL - padR);

  const step = max > 4 ? 1 : 0.5;
  const ticks = [];
  for (let t = 0; t <= max; t += step) ticks.push(t);

  return (
    <div ref={boxRef}>
      <svg className="strip" viewBox={`0 0 ${width} ${height}`} height={height}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={x(t)} y1={padT} x2={x(t)} y2={height - padB} stroke="var(--rule-soft)" />
            <text x={x(t)} y={height - padB + 16} fontSize="11" fill="var(--muted)" textAnchor="middle">
              {t}
            </text>
          </g>
        ))}
        <text x={width - padR} y={height - padB + 16} fontSize="11" fill="var(--muted)" textAnchor="end">
          오차 [m]
        </text>

        {usable.map((r, i) => {
          const y = padT + i * rowH + rowH / 2;
          const color = r.reliable ? "var(--signal)" : "var(--tick)";
          const prev = usable[i - 1]?.target_speed;
          const changed =
            prev && r.target_speed &&
            Math.max(prev, r.target_speed) / Math.min(prev, r.target_speed) > 1.25;
          return (
            <g key={r.experiment_id}>
              {changed && (
                <>
                  <line
                    x1={padL - 24} y1={y - rowH / 2} x2={width - padR} y2={y - rowH / 2}
                    stroke="var(--caution)" strokeDasharray="3 3"
                  />
                  <text
                    x={width - padR} y={y - rowH / 2 - 4} fontSize="10"
                    fill="var(--caution)" textAnchor="end"
                  >
                    표적 속도 {prev} → {r.target_speed} m/s
                  </text>
                </>
              )}
              <text x={padL - 10} y={y + 4} fontSize="12" fill="var(--muted)" textAnchor="end">
                {r.run_no}
              </text>
              <line x1={x(r.best)} y1={y} x2={x(r.worst)} y2={y} stroke="var(--rule)" />
              {r.shots.map((m, k) => (
                <line key={k} x1={x(m)} y1={y - 6} x2={x(m)} y2={y + 6} stroke={color} opacity="0.5" />
              ))}
              <line x1={x(r.median)} y1={y - 9} x2={x(r.median)} y2={y + 9} stroke={color} strokeWidth="2.5" />
            </g>
          );
        })}
      </svg>
    </div>
  );
}
