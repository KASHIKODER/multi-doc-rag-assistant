"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { Button } from "@/components/ui/Button";

type QuestionInputProps = {
  value?: string;
  defaultQuestion?: string;
  demoQuestions: readonly string[];
  loading?: boolean;
  onChange?: (value: string) => void;
  onSubmit?: () => void;
};

export function QuestionInput({
  value,
  defaultQuestion = "What are selectors?",
  demoQuestions,
  loading = false,
  onChange,
  onSubmit,
}: QuestionInputProps) {
  const [internalValue, setInternalValue] = useState(defaultQuestion);

  const isControlled = typeof value === "string";
  const currentValue = isControlled ? value : internalValue;

  function updateQuestion(nextValue: string) {
    if (isControlled) {
      onChange?.(nextValue);
      return;
    }

    setInternalValue(nextValue);
    onChange?.(nextValue);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!currentValue.trim() || loading) {
      return;
    }

    onSubmit?.();
  }

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm font-semibold text-[#2563EB]">
        Question workspace
      </p>

      <h2 className="mt-2 text-xl font-semibold text-[#0F172A]">
        Ask across your indexed documents
      </h2>

      <form onSubmit={handleSubmit}>
        <div className="mt-5">
          <label
            htmlFor="question"
            className="text-sm font-medium text-slate-700"
          >
            Question
          </label>

          <textarea
            id="question"
            rows={5}
            value={currentValue}
            onChange={(event) => updateQuestion(event.target.value)}
            disabled={loading}
            className="mt-2 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-[#0F172A] outline-none transition focus:border-[#2563EB] focus:bg-white disabled:cursor-not-allowed disabled:opacity-70"
            placeholder="Ask something about your indexed documents..."
          />
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {demoQuestions.map((question) => (
            <button
              key={question}
              type="button"
              disabled={loading}
              onClick={() => updateQuestion(question)}
              className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-[#2563EB] hover:text-[#0F172A] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {question}
            </button>
          ))}
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <Button
            type="submit"
            disabled={!currentValue.trim() || loading}
          >
            {loading ? "Running pipeline..." : "Run RAG Pipeline"}
          </Button>

          <Button
            type="button"
            variant="secondary"
            disabled={loading}
            onClick={() => updateQuestion("")}
          >
            Clear
          </Button>
        </div>
      </form>
    </section>
  );
}
