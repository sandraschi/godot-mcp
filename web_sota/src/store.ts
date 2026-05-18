import { create } from "zustand";

interface AppState {
	connectionStatus: "connected" | "disconnected" | "connecting";
	serverVersion: string;
	godotAvailable: boolean;
	theme: "dark";
	setConnectionStatus: (status: AppState["connectionStatus"]) => void;
	setServerVersion: (version: string) => void;
	setGodotAvailable: (available: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
	connectionStatus: "connecting",
	serverVersion: "",
	godotAvailable: false,
	theme: "dark",
	setConnectionStatus: (status) => set({ connectionStatus: status }),
	setServerVersion: (version) => set({ serverVersion: version }),
	setGodotAvailable: (available) => set({ godotAvailable: available }),
}));
