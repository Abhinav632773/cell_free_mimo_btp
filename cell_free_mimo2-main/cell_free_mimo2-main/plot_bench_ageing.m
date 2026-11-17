%% =========================================================================
% plot_bench_ageing.m
% 
% Fetches data from: Table3_E2_ageing_qnnassignmr.csv & Table3_E2_ageing_search.csv
% Generates: Benchmark E2 CSI Ageing vs. Decision Delay across Speeds
%   (1) QNN Assignment + MR (Proposed)
%   (2) Search-based + MR (Baseline)
%
% Matches the benchmark results in "bench_E2_ageing.png".
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

candidateQNN = {
    fullfile(scriptDir, 'Table3_E2_ageing_qnnassignmr.csv'), ...
    fullfile(pwd, 'Table3_E2_ageing_qnnassignmr.csv'), ...
    fullfile(scriptDir, 'results', 'Table3_E2_ageing_qnnassignmr.csv'), ...
    fullfile(pwd, 'results', 'Table3_E2_ageing_qnnassignmr.csv'), ...
    fullfile(scriptDir, '..', 'cell_free_mimo2-main', 'results', 'Table3_E2_ageing_qnnassignmr.csv')
};

candidateSearch = {
    fullfile(scriptDir, 'Table3_E2_ageing_search.csv'), ...
    fullfile(pwd, 'Table3_E2_ageing_search.csv'), ...
    fullfile(scriptDir, 'results', 'Table3_E2_ageing_search.csv'), ...
    fullfile(pwd, 'results', 'Table3_E2_ageing_search.csv'), ...
    fullfile(scriptDir, '..', 'cell_free_mimo2-main', 'results', 'Table3_E2_ageing_search.csv')
};

csvQNN = '';
for i = 1:numel(candidateQNN)
    if exist(candidateQNN{i}, 'file')
        csvQNN = candidateQNN{i};
        break;
    end
end

csvSearch = '';
for i = 1:numel(candidateSearch)
    if exist(candidateSearch{i}, 'file')
        csvSearch = candidateSearch{i};
        break;
    end
end

if isempty(csvQNN) || isempty(csvSearch)
    error('Could not find Table3_E2 ageing CSV files in %s or %s', scriptDir, pwd);
end

fprintf('\n-------------------------------------------------------------\n');
fprintf('  Running: plot_bench_ageing.m\n');
fprintf('  Data QNN:    %s\n', csvQNN);
fprintf('  Data Search: %s\n', csvSearch);
fprintf('-------------------------------------------------------------\n');

outputFigPath    = fullfile(scriptDir, 'matlab_bench_E2_ageing.png');
outputFigPathFig = fullfile(scriptDir, 'matlab_bench_E2_ageing.fig');

% --- Figure Window Properties ---
figWidth  = 1150;    % Width in pixels
figHeight = 520;     % Height in pixels
fontName  = 'Helvetica';
titleFontSize  = 12.5;
labelFontSize  = 11.0;
axisFontSize   = 10.0;
legendFontSize = 10.0;
superTitleFontSize = 14.5;

% --- Delay Grid [ms] ---
delays_ms = [0, 0.25, 0.5, 1.0, 2.0, 5.0];

% --- Speed Line Colors & Markers ---
speedColors = {
    [0.15, 0.40, 0.85], ... % 20 km/h: Blue
    [0.85, 0.35, 0.10], ... % 40 km/h: Orange
    [0.15, 0.70, 0.25], ... % 80 km/h: Green
    [0.80, 0.15, 0.20]      % 120 km/h: Red
};
markers = {'o', 's', '^', 'd'};
lineWidth = 2.0;

% --- Grid Properties ---
enableGrid    = true;
gridLineStyle = '--';
gridAlpha     = 0.45;

%% =========================================================================
%% 2. DATA IMPORT
%% =========================================================================

try
    TQNN = readtable(csvQNN, 'VariableNamingRule', 'preserve');
    TSearch = readtable(csvSearch, 'VariableNamingRule', 'preserve');
catch
    TQNN = readtable(csvQNN);
    TSearch = readtable(csvSearch);
end

% Extract numeric rates: Columns 2 through 7 correspond to 0, 0.25, 0.5, 1, 2, 5 ms
ratesQNN    = TQNN{:, 2:7};
ratesSearch = TSearch{:, 2:7};
speeds      = TQNN{:, 1};

%% =========================================================================
%% 3. PLOTTING (1x2 GRID: QNN vs SEARCH)
%% =========================================================================

fig = figure('Name', 'Benchmark E2: CSI Ageing', 'Color', 'w', ...
    'Position', [100, 150, figWidth, figHeight], 'NumberTitle', 'off');

% --- Subplot 1: QNN Assignment + MR ---
subplot(1, 2, 1);
hold on; box on;
for s = 1:length(speeds)
    plot(delays_ms, ratesQNN(s, :), '-', 'Color', speedColors{s}, ...
        'LineWidth', lineWidth, 'Marker', markers{s}, 'MarkerSize', 7, ...
        'MarkerFaceColor', speedColors{s}, 'DisplayName', sprintf('%g km/h', speeds(s)));
end
title('QNN Assignment + MR', 'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel('Decision Delay \Delta [ms]', 'FontSize', labelFontSize, 'FontName', fontName);
ylabel('Avg Min Rate [bits/s/Hz]', 'FontSize', labelFontSize, 'FontName', fontName);
set(gca, 'FontName', fontName, 'FontSize', axisFontSize, 'LineWidth', 1.0);
legend('Location', 'northeast', 'FontSize', legendFontSize);
if enableGrid
    grid on; ax = gca; ax.GridLineStyle = gridLineStyle; ax.GridAlpha = gridAlpha;
end
hold off;

% --- Subplot 2: Search-based + MR ---
subplot(1, 2, 2);
hold on; box on;
for s = 1:length(speeds)
    plot(delays_ms, ratesSearch(s, :), '-', 'Color', speedColors{s}, ...
        'LineWidth', lineWidth, 'Marker', markers{s}, 'MarkerSize', 7, ...
        'MarkerFaceColor', speedColors{s}, 'DisplayName', sprintf('%g km/h', speeds(s)));
end
title('Search-based + MR', 'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel('Decision Delay \Delta [ms]', 'FontSize', labelFontSize, 'FontName', fontName);
ylabel('Avg Min Rate [bits/s/Hz]', 'FontSize', labelFontSize, 'FontName', fontName);
set(gca, 'FontName', fontName, 'FontSize', axisFontSize, 'LineWidth', 1.0);
legend('Location', 'northeast', 'FontSize', legendFontSize);
if enableGrid
    grid on; ax = gca; ax.GridLineStyle = gridLineStyle; ax.GridAlpha = gridAlpha;
end
hold off;

% Global Super-Title
if exist('sgtitle', 'file') || exist('sgtitle', 'builtin')
    sgtitle('Benchmark E2: CSI Ageing on the Realistic V2X Channel', ...
        'FontSize', superTitleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
else
    annotation('textbox', [0 0.9 1 0.1], 'String', 'Benchmark E2: CSI Ageing on V2X Channel', ...
        'EdgeColor', 'none', 'HorizontalAlignment', 'center', ...
        'FontSize', superTitleFontSize, 'FontWeight', 'bold');
end

% Flush rendering so figure is ready for saving
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
    fprintf('[OK] Saved figure (.fig format): %s\n', outputFigPathFig);
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
    fprintf('[OK] Saved image (.png format): %s\n', outputFigPath);
end

% Also mirror to Current Working Directory if different
if ~strcmp(pwd, scriptDir)
    try
        if savedFig, copyfile(outputFigPathFig, fullfile(pwd, 'matlab_bench_E2_ageing.fig')); end
        if savedPng, copyfile(outputFigPath, fullfile(pwd, 'matlab_bench_E2_ageing.png')); end
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
fprintf('  Benchmark E2 plot completed successfully!\n');
fprintf('-------------------------------------------------------------\n\n');
