import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Text wrapping algorithm
const wrapText = (text, maxLength = 12) => {
  if (!text) return [];
  const rawWords = String(text).split(" ");
  const lines = [];
  let currentLine = "";
  
  for (let word of rawWords) {
    if (word.includes("-")) {
      const subWords = word.split("-");
      for (let i = 0; i < subWords.length; i++) {
        const subWord = subWords[i] + (i < subWords.length - 1 ? "-" : "");
        if (!currentLine) {
          currentLine = subWord;
        } else if (currentLine.length + subWord.length > maxLength) {
          lines.push(currentLine);
          currentLine = subWord;
        } else {
          currentLine += (currentLine.endsWith("-") ? "" : " ") + subWord;
        }
      }
    } else {
      if (!currentLine) {
        currentLine = word;
      } else if (currentLine.length + word.length > maxLength) {
        lines.push(currentLine);
        currentLine = word;
      } else {
        currentLine += " " + word;
      }
    }
  }
  if (currentLine) {
    lines.push(currentLine);
  }
  return lines;
};

// Reusable custom XAxis tick component
export const CustomXAxisTick = (props) => {
  const { x, y, payload, stroke } = props;
  const val = payload.value;
  const lines = wrapText(val);

  return (
    <g transform={`translate(${x},${y})`}>
      <text
        x={0}
        y={0}
        textAnchor="middle"
        fill={stroke}
        fontSize="11px"
        fontWeight="500"
        className="fill-slate-500 dark:fill-slate-400"
      >
        {lines.map((line, index) => (
          <tspan key={index} x={0} dy={index === 0 ? 12 : 14}>
            {line}
          </tspan>
        ))}
      </text>
    </g>
  );
};

export const CustomBarChart = ({
  data,
  dataKey,
  barKey,
  barColor,
  axisColor,
  gridColor,
  tooltipBg,
  tooltipBorder,
  tooltipText,
  labelName
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center text-xs text-slate-400">
        No data available
      </div>
    );
  }

  // Calculate dynamic bottom margin based on the longest wrapped label
  const maxLines = Math.max(...data.map(d => wrapText(d[dataKey] || "").length), 1);
  const bottomMargin = Math.max(50, maxLines * 14 + 20); // e.g. 1 line -> 50px, 3 lines -> 62px, 4 lines -> 76px

  // Automatically increase chart width and enable horizontal scrolling if there are many bars
  const minWidth = Math.max(100, data.length * 80);

  return (
    <div className="w-full overflow-x-auto scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-800 scrollbar-track-transparent">
      <div style={{ width: "100%", minWidth: `${minWidth}px`, height: "260px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: bottomMargin }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis
              dataKey={dataKey}
              stroke={axisColor}
              tickLine={false}
              interval={0}
              tick={<CustomXAxisTick stroke={axisColor} />}
            />
            <YAxis stroke={axisColor} fontSize={10} tickLine={false} />
            <Tooltip contentStyle={{ backgroundColor: tooltipBg, borderColor: tooltipBorder, color: tooltipText }} />
            <Bar dataKey={barKey} fill={barColor} radius={[4, 4, 0, 0]} name={labelName} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
