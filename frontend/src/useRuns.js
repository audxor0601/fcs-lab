import { useEffect, useState } from "react";
import { fetchMissValues, fetchRuns } from "./api";

/**
 * 회차 목록과 각 회차의 개별 탄착을 불러온다.
 * 분포도가 개별 탄착을 필요로 해서, 요약만으로는 부족하다.
 */
export function useRuns() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const { runs } = await fetchRuns();
        const withShots = await Promise.all(
          runs.map(async (r) =>
            r.n > 0 ? { ...r, shots: await fetchMissValues(r.experiment_id) } : { ...r, shots: [] }
          )
        );
        if (!cancelled) setRuns(withShots);
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  return { runs, loading, error };
}
