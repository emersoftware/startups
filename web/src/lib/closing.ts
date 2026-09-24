export type ClosingSource = {
  label: string;
  url?: string;
  basis?: string;
};

export type ClosingParagraph = {
  text: string;
  sources: ClosingSource[];
};

export type Closing = {
  reviewed_on: string | null;
  summary: ClosingParagraph[];
  details: ClosingParagraph[];
};
