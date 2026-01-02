// PuzzleGrid.jsx
import React from 'react';

const PuzzleGrid = ({ grid, onSelect }) => {
  return (
    <div className="grid">
      {grid.map((row, rowIndex) => (
        <div key={rowIndex} className="row">
          {row.map((letter, colIndex) => (
            <button
              key={colIndex}
              className="cell"
              onClick={() => onSelect(rowIndex, colIndex)}
            >
              {letter}
            </button>
          ))}
        </div>
      ))}
    </div>
  );
};

export default PuzzleGrid;