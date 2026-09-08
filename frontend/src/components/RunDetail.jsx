import { useEffect, useState } from "react";
import { fetchRunDetail } from "../api";
import { fmt, ZONE_LABEL } from "../format";

export default function RunDetail({ id }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setData(null);
    setError(null);

    fetchRunDetail(id)
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && setError(e.message));

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) return <p className="empty">상세를 불러오지 못했다. ({error})</p>;
  if (!data) return <p className="empty">불러오는 중</p>;

  const o = data.overall;
  if (o.n === 0) {
    return (
      <>
        <div className="detail-head">
          <h2>{data.name}</h2>
        </div>
        <p className="empty">이 회차에는 사격 기록이 없다.</p>
      </>
    );
  }

  const maxZone = Math.max(...data.by_zone.map((z) => z.median || 0));

  return (
    <>
      <div className="detail-head">
        <h2>{data.name}</h2>
        <span>
          {o.n}발 분석 · 중앙값 {fmt(o.median)} m
        </span>
      </div>

      {data.warning && <div className="warn">{data.warning}</div>}

      <div className="grid">
        <div>
          <p className="sub">표적 방향별 오차 중앙값 [m]</p>
          {data.by_zone.map((z) => (
            <div className="bar-row" key={z.zone}>
              <span>{ZONE_LABEL[z.zone] || z.zone}</span>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{ width: `${maxZone ? (z.median / maxZone) * 100 : 0}%` }}
                />
              </div>
              <span className="bar-val">
                {fmt(z.median)} <span className="bar-n">{z.n}</span>
              </span>
            </div>
          ))}
        </div>

        <div>
          <p className="sub">오차와 함께 움직이는 값</p>
          {data.correlations.map((c) => (
            <div className="corr" key={c.field}>
              <div className="corr-top">
                <span>{c.label}</span>
                <span className="corr-r">{c.r === null ? "—" : c.r}</span>
              </div>
              <div className="corr-say">{c.interpretation}</div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
