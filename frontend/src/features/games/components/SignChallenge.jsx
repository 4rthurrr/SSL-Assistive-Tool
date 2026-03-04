// SignChallenge.jsx
import React, { useState, useEffect } from 'react';
import PuzzleGrid from '../puzzle/PuzzleGrid';

const SignChallenge = () => {
  const [signData, setSignData] = useState(null);
  const [grid, setGrid] = useState([]);

  useEffect(() => {
    fetch('/api/signs/random')
      .then(res => res.json())
      .then(data => {
        setSignData(data);
        setGrid(generatePuzzleGrid(data.word));
      });
  }, []);

  const generatePuzzleGrid = (word) => {
    // Create a grid with the word hidden among random letters
    // You can customize this logic
    const gridSize = 10;
    const grid = Array(gridSize).fill().map(() =>
      Array(gridSize).fill().map(() =>
        String.fromCharCode(65 + Math.floor(Math.random() * 26))
      )
    );
    // Insert word horizontally for now
    const row = Math.floor(Math.random() * gridSize);
    const col = Math.floor(Math.random() * (gridSize - word.length));
    for (let i = 0; i < word.length; i++) {
      grid[row][col + i] = word[i].toUpperCase();
    }
    return grid;
  };

  return (
    <div>
      {signData && (
        <>
          <img src={signData.imageUrl} alt="Sign" style={{ width: '200px' }} />
          <PuzzleGrid grid={grid} onSelect={(r, c) => console.log(r, c)} />
        </>
      )}
    </div>
  );
};

export default SignChallenge;