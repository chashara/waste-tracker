import { useEffect, useState } from "react";

export function useAsync(fn, deps) {
  const key = JSON.stringify(deps);
  const [state, setState] = useState({ key: null, data: null, error: "" });

  useEffect(() => {
    let cancelled = false;
    fn()
      .then((data) => {
        if (!cancelled) setState({ key, data, error: "" });
      })
      .catch((err) => {
        if (!cancelled) setState({ key, data: null, error: err.message });
      });
    return () => {
      cancelled = true; // ignore answers that arrive after the filters changed again
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return {
    data: state.data,
    error: state.key === key ? state.error : "",
    loading: state.key !== key,
  };
}