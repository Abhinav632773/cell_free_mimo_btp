%% =========================================================================
% plot_bench_channels.m
% 
% Fetches data from: Table2_E1_channels.csv
% Generates: Benchmark E1 Channel Comparison (i.i.d. Rayleigh vs. V2X One-Ring)
%   (1) Average User Min Rate [bits/s/Hz]
%   (2) Average Network Sum Rate [bits/s/Hz]
%
% Matches the benchmark results in "bench_E1_channels.png".
% Saves both .fig (native MATLAB figure) and high-res .png formats.
% =========================================================================

close all;

%% =========================================================================
%% 1. EDITABLE PARAMETERS (CUSTOMIZE AXES, LABELS, COLORS, FONTS HERE)
%% =========================================================================

% --- File Paths (Auto-resolves relative to script directory) ---
scriptDir = fileparts(mfilename('fullpath'));
if isempty(scriptDir)
    scriptDir = pwd;
end

candidateCsvPaths = {
    fullfile(scriptDir, 'Table2_E1_channels.csv'), ...
    fullfile(scriptDir, 'results', 'Table2_E1_channels.csv'), ...
    fullfile(pwd, 'Table2_E1_channels.csv'), ...
    fullfile(pwd, 'results', 'Table2_E1_channels.csv'), ...
    fullfile(scriptDir, '..', 'cell_free_mimo2-main', 'results', 'Table2_E1_channels.csv')
};

csvFilePath = '';
for i = 1:numel(candidateCsvPaths)
    if exist(candidateCsvPaths{i}, 'file')
        csvFilePath = candidateCsvPaths{i};
        break;
    end
end

if isempty(csvFilePath)
    error(['Could not find data file "Table2_E1_channels.csv".\n' ...
           'Please ensure Table2_E1_channels.csv is in the script folder.']);
end

outputFigPath    = fullfile(scriptDir, 'matlab_bench_E1_channels.png');
outputFigPathFig = fullfile(scriptDir, 'matlab_bench_E1_channels.fig');

% --- Figure Window Properties ---
figWidth  = 1150;    % Width in pixels
figHeight = 550;     % Height in pixels
fontName  = 'Helvetica';
titleFontSize  = 12.5;
labelFontSize  = 11.5;
axisFontSize   = 10.0;
legendFontSize = 10.5;
superTitleFontSize = 14.5;

% --- Bar Colors ---
c_iid = [0.20, 0.45, 0.85];   % Blue for i.i.d. Rayleigh
c_v2x = [0.85, 0.40, 0.15];   % Orange for V2X One-Ring

% --- Grid Properties ---
enableGrid    = true;
gridLineStyle = '--';
gridAlpha     = 0.45;

%% =========================================================================
%% 2. DATA IMPORT & PARSING
%% =========================================================================

try
    T = readtable(csvFilePath, 'VariableNamingRule', 'preserve');
catch
    T = readtable(csvFilePath);
end

methods = string(T{:, 1});
numMethods = length(methods);

% Helper to parse "0.632 ± 0.000" or raw numbers
parse_val = @(strVal) sscanf(regexprep(char(strVal), '±.*', ''), '%f');

minRate_iid = zeros(numMethods, 1);
minRate_v2x = zeros(numMethods, 1);
sumRate_iid = zeros(numMethods, 1);
sumRate_v2x = zeros(numMethods, 1);

for i = 1:numMethods
    minRate_iid(i) = parse_val(T{i, 2});
    minRate_v2x(i) = parse_val(T{i, 3});
    sumRate_iid(i) = parse_val(T{i, 4});
    sumRate_v2x(i) = parse_val(T{i, 5});
end

%% =========================================================================
%% 3. PLOTTING (1x2 GRID: MIN RATE & SUM RATE)
%% =========================================================================

fig = figure('Color', 'w', 'Position', [100, 150, figWidth, figHeight]);

% --- Subplot 1: Min Rate ---
subplot(1, 2, 1);
b1 = bar([minRate_iid, minRate_v2x], 0.8);
b1(1).FaceColor = c_iid;
b1(2).FaceColor = c_v2x;
title('Min User Rate Comparison (Fairness)', 'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel('Beamforming / Association Method', 'FontSize', labelFontSize, 'FontName', fontName);
ylabel('Min Rate [bits/s/Hz]', 'FontSize', labelFontSize, 'FontName', fontName);
set(gca, 'XTickLabel', methods, 'XTickLabelRotation', 20, 'FontName', fontName, 'FontSize', axisFontSize);
legend({'i.i.d. Rayleigh', 'V2X One-Ring'}, 'Location', 'northeast', 'FontSize', legendFontSize);
if enableGrid
    grid on; ax = gca; ax.GridLineStyle = gridLineStyle; ax.GridAlpha = gridAlpha;
end

% --- Subplot 2: Sum Rate ---
subplot(1, 2, 2);
b2 = bar([sumRate_iid, sumRate_v2x], 0.8);
b2(1).FaceColor = c_iid;
b2(2).FaceColor = c_v2x;
title('Sum Rate Comparison (Throughput)', 'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel('Beamforming / Association Method', 'FontSize', labelFontSize, 'FontName', fontName);
ylabel('Sum Rate [bits/s/Hz]', 'FontSize', labelFontSize, 'FontName', fontName);
set(gca, 'XTickLabel', methods, 'XTickLabelRotation', 20, 'FontName', fontName, 'FontSize', axisFontSize);
legend({'i.i.d. Rayleigh', 'V2X One-Ring'}, 'Location', 'northeast', 'FontSize', legendFontSize);
if enableGrid
    grid on; ax = gca; ax.GridLineStyle = gridLineStyle; ax.GridAlpha = gridAlpha;
end

% Global Super-Title
if exist('sgtitle', 'file') || exist('sgtitle', 'builtin')
    sgtitle('Benchmark E1: Small-Scale Channel Impact (i.i.d. Rayleigh vs. V2X One-Ring)', ...
        'FontSize', superTitleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
else
    annotation('textbox', [0 0.9 1 0.1], 'String', 'Benchmark E1: Small-Scale Channel Impact', ...
        'EdgeColor', 'none', 'HorizontalAlignment', 'center', ...
        'FontSize', superTitleFontSize, 'FontWeight', 'bold');
end

%% =========================================================================
%% 4. EXPORT HIGH-RESOLUTION FIGURE & MATLAB .FIG FORMAT
%% =========================================================================

drawnow;
pause(0.2);

if ~exist('fig', 'var') || isempty(fig) || ~isgraphics(fig, 'figure')
    fig = gcf;
end
if isgraphics(fig, 'figure')
    figure(fig);
end
drawnow;

outDir = fileparts(outputFigPath);
if ~isempty(outDir) && ~exist(outDir, 'dir')
    mkdir(outDir);
end

% 1. Save native MATLAB .fig format
savedFig = false;
try
    savefig(fig, outputFigPathFig);
    savedFig = true;
catch
    try
        saveas(fig, outputFigPathFig);
        savedFig = true;
    catch
        try
            figure(fig);
            savefig(outputFigPathFig);
            savedFig = true;
        catch ME_fig
            warning('Could not save .fig file: %s', ME_fig.message);
        end
    end
end
if savedFig
    fprintf('[OK] Benchmark E1 plot (.fig format) saved to: %s\n', outputFigPathFig);
end

% 2. Save high-resolution PNG
savedPng = false;
try
    if exist('exportgraphics', 'file') || exist('exportgraphics', 'builtin')
        exportgraphics(fig, outputFigPath, 'Resolution', 300);
        savedPng = true;
    else
        print(fig, outputFigPath, '-dpng', '-r300');
        savedPng = true;
    end
catch
    try
        saveas(fig, outputFigPath);
        savedPng = true;
    catch ME_png
        warning('Could not save .png image: %s', ME_png.message);
    end
end
if savedPng
    fprintf('[OK] Benchmark E1 plot (.png format) saved to: %s\n', outputFigPath);
end

% Also mirror to Current Working Directory if different
if ~strcmp(pwd, scriptDir)
    try
        if savedFig, copyfile(outputFigPathFig, fullfile(pwd, 'matlab_bench_E1_channels.fig')); end
        if savedPng, copyfile(outputFigPath, fullfile(pwd, 'matlab_bench_E1_channels.png')); end
        fprintf('[OK] Also copied output files to current folder: %s\n', pwd);
    catch
    end
end

% Refresh MATLAB current folder
try
    rehash;
catch
end

fprintf('-------------------------------------------------------------\n');
fprintf('  Benchmark E1 Channel Comparison plot completed!\n');
fprintf('-------------------------------------------------------------\n\n');

