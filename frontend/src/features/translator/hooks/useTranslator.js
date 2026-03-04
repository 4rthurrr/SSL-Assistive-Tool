import { useState, useCallback } from 'react';
import { translatorAPI } from '../../../utils/api';

export const useTranslator = () => {
  const [videoUrl, setVideoUrl] = useState(null);
  const [grammarSequence, setGrammarSequence] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const translate = useCallback(async (text) => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setVideoUrl(null);
    setGrammarSequence([]);
    try {
      const data = await translatorAPI.translate(text);
      if (data.video_url) setVideoUrl(data.video_url);
      if (data.grammar_sequence) setGrammarSequence(data.grammar_sequence);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { videoUrl, grammarSequence, loading, error, translate };
};
