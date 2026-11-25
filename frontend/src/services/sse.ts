export interface ParsedSseEvent {
  event?: string;
  data: string;
}

export class SseParser {
  private buffer = "";

  push(chunk: string, flush = false): ParsedSseEvent[] {
    this.buffer += chunk.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    const events: ParsedSseEvent[] = [];
    let boundary = this.buffer.indexOf("\n\n");
    while (boundary >= 0) {
      const block = this.buffer.slice(0, boundary);
      this.buffer = this.buffer.slice(boundary + 2);
      const event = parseBlock(block);
      if (event) events.push(event);
      boundary = this.buffer.indexOf("\n\n");
    }
    if (flush && this.buffer.trim()) {
      const event = parseBlock(this.buffer);
      if (event) events.push(event);
      this.buffer = "";
    }
    return events;
  }
}

function parseBlock(block: string): ParsedSseEvent | null {
  let event: string | undefined;
  const data: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
  }
  return data.length
    ? event === undefined
      ? { data: data.join("\n") }
      : { event, data: data.join("\n") }
    : null;
}
