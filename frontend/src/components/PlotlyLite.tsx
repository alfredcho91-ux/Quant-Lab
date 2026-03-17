import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js/lib/core';
import candlestick from 'plotly.js/lib/candlestick';
import scatter from 'plotly.js/lib/scatter';

// Register only traces used by our chart to reduce bundle size.
Plotly.register([candlestick, scatter]);

const Plot = createPlotlyComponent(Plotly);

export default Plot;
