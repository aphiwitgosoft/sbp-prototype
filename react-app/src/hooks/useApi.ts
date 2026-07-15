import { useCallback, useEffect, useRef, useState } from 'react';
import { apiGet, type QueryParams } from '@/lib/api';

interface State<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/** ดึงข้อมูล GET แบบง่าย — คืน { data, loading, error, refetch } */
export function useApi<T>(path: string | null, params?: QueryParams) {
  const [state, setState] = useState<State<T>>({ data: null, loading: !!path, error: null });
  // serialize params เพื่อใช้เป็น dependency
  const key = params ? JSON.stringify(params) : '';
  const mounted = useRef(true);

  const run = useCallback(() => {
    if (!path) return;
    setState((s) => ({ ...s, loading: true, error: null }));
    apiGet<T>(path, params)
      .then((data) => mounted.current && setState({ data, loading: false, error: null }))
      .catch((e: Error) =>
        mounted.current && setState({ data: null, loading: false, error: e.message }),
      );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, key]);

  useEffect(() => {
    mounted.current = true;
    run();
    return () => {
      mounted.current = false;
    };
  }, [run]);

  return { ...state, refetch: run };
}
