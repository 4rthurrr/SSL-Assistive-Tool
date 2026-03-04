import { useState, useCallback } from 'react';
import { gameAPI } from '../../../utils/api';

export const useGameLogic = () => {
  const [score, setScore] = useState(0);
  const [level, setLevel] = useState('basic');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadQuestions = useCallback(async (grade) => {
    setLoading(true);
    setError(null);
    try {
      return await gameAPI.getQuestions(grade);
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const submitAttempt = useCallback(async (attemptData) => {
    try {
      return await gameAPI.saveAttempt(attemptData);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  return { score, setScore, level, setLevel, loading, error, loadQuestions, submitAttempt };
};
