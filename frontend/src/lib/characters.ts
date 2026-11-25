import atlas from "@/assets/atlas.asset.json";
import luna from "@/assets/luna.asset.json";
import nova from "@/assets/nova.asset.json";
import echo from "@/assets/echo.asset.json";

export type CharacterId = "atlas" | "luna" | "nova" | "echo";
export interface Character {
  id: CharacterId;
  name: string;
  category: string;
  image: string;
  tone: string;
}
export const characters: Character[] = [
  { id: "atlas", name: "Atlas", category: "tech", image: atlas.url, tone: "electric" },
  { id: "luna", name: "Luna", category: "creative", image: luna.url, tone: "violet" },
  { id: "nova", name: "Nova", category: "productivity", image: nova.url, tone: "success" },
  { id: "echo", name: "Echo", category: "story", image: echo.url, tone: "warning" },
];
