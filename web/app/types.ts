export type Source = {
  id: string;
  doc_id: string;
  title: string;
  url: string;
  fetched_at: string;
  cited: boolean;
  excerpt?: string;
};

export type AskResponse = {
  request_id: string;
  answer: string | null;
  refused: boolean;
  reason: string;
  lang: string;
  cited?: string[];
  sources: Source[];
  valid_as_of: string;
  disclaimer: string;
  note?: string;
};
