import { useCallback, useEffect, useRef } from "react";

const ZOOM_LEVELS = [0.8, 1.0, 1.25, 1.5, 2.0, 3.0];

function loadZoomIndex(): number {
	try {
		const saved = localStorage.getItem("tauri-zoom");
		return saved ? ZOOM_LEVELS.indexOf(Number.parseFloat(saved)) : 1;
	} catch {
		return 1;
	}
}

export default function useZoom() {
	const index = useRef(loadZoomIndex());

	const applyZoom = useCallback(async (level: number) => {
		localStorage.setItem("tauri-zoom", String(level));
		try {
			const { getCurrentWindow } = await import("@tauri-apps/api/window");
			const w = getCurrentWindow() as unknown as { setZoom: (level: number) => Promise<void> };
			await w.setZoom(level);
		} catch {
			// Dev browser fallback: CSS scale on root
			const root = document.documentElement;
			root.style.transform = `scale(${level})`;
			root.style.transformOrigin = "top left";
			root.style.width = `${100 / level}%`;
			root.style.height = `${100 / level}%`;
		}
	}, []);

	useEffect(() => {
		applyZoom(ZOOM_LEVELS[index.current]);
		const handler = (e: WheelEvent) => {
			if (!e.ctrlKey) return;
			e.preventDefault();
			const delta = e.deltaY < 0 ? 1 : -1;
			const next = Math.min(Math.max(index.current + delta, 0), ZOOM_LEVELS.length - 1);
			if (next !== index.current) {
				index.current = next;
				applyZoom(ZOOM_LEVELS[next]);
			}
		};
		window.addEventListener("wheel", handler, { passive: false });
		return () => window.removeEventListener("wheel", handler);
	}, [applyZoom]);
}
