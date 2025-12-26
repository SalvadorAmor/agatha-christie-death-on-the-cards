import { renderHook, act } from "@testing-library/react";
import useJustAdded from "./useJustAdded";

describe("useJustAdded", () => {
  it("devuelve un set vacío al inicio", () => {
    const { result } = renderHook(() => useJustAdded([]));
    expect(result.current.size).toBe(0);
  });

  it("no marca nada como agregado en el primer render", () => {
    const items = [{ id: 1 }, { id: 2 }];
    const { result } = renderHook(() => useJustAdded(items));
    expect(result.current.size).toBe(0);
  });

  it("detecta un nuevo elemento agregado", () => {
    let items = [{ id: 1 }, { id: 2 }];
    const { result, rerender } = renderHook(
      (props) => useJustAdded(props),
      { initialProps: items }
    );

    act(() => {
      items = [...items, { id: 3 }];
      rerender(items);
    });

    expect(result.current.has(3)).toBe(true);
  });

  it("no marca como nuevos los elementos existentes", () => {
    let items = [{ id: 1 }, { id: 2 }];
    const { result, rerender } = renderHook(
      (props) => useJustAdded(props),
      { initialProps: items }
    );

    act(() => {
      // mismo conjunto, orden diferente
      items = [{ id: 2 }, { id: 1 }];
      rerender(items);
    });

    expect(result.current.size).toBe(0);
  });

  it("detecta varios nuevos elementos a la vez", () => {
    let items = [{ id: 1 }];
    const { result, rerender } = renderHook(
      (props) => useJustAdded(props),
      { initialProps: items }
    );

    act(() => {
      items = [{ id: 1 }, { id: 2 }, { id: 3 }];
      rerender(items);
    });

    expect(result.current.has(2)).toBe(true);
    expect(result.current.has(3)).toBe(true);
  });

  it("acumula correctamente nuevos items entre renders", () => {
    let items = [{ id: 1 }];
    const { result, rerender } = renderHook(
      (props) => useJustAdded(props),
      { initialProps: items }
    );

    act(() => {
      items = [...items, { id: 2 }];
      rerender(items);
    });
    act(() => {
      items = [...items, { id: 3 }];
      rerender(items);
    });

    expect(result.current.has(2)).toBe(true);
    expect(result.current.has(3)).toBe(true);
  });
});
