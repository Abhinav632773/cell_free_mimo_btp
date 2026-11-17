%% =========================================================================
% plot_training_overview.m
% 
% Fetches data from: training_history.csv (same folder or results/)
% Generates: 2x2 Training Overview (Cloud Loss, Edge Loss, Min Rate, Sum Rate)
%
% All styling parameters (axes limits, labels, colors, font sizes, line widths)
% are organized in the EDITABLE PARAMETERS section below for easy modification.
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
    fullfile(scriptDir, 'training_history.csv'), ...
    fullfile(pwd, 'training_history.csv'), ...
    fullfile(scriptDir, 'results', 'training_history.csv'), ...
    fullfile(pwd, 'results', 'training_history.csv'), ...
    fullfile(scriptDir, '..', 'cell_free_mimo2-main', 'results', 'training_history.csv'), ...
    fullfile(scriptDir, '..', 'final_res', 'training_history.csv')
};

csvFilePath = '';
for i = 1:numel(candidateCsvPaths)
    if exist(candidateCsvPaths{i}, 'file')
        csvFilePath = candidateCsvPaths{i};
        break;
    end
end

if isempty(csvFilePath)
    error('Could not find training_history.csv in %s or %s', scriptDir, pwd);
end

fprintf('\n-------------------------------------------------------------\n');
fprintf('  Running: plot_training_overview.m\n');
fprintf('  Data file: %s\n', csvFilePath);
fprintf('-------------------------------------------------------------\n');

if isempty(csvFilePath)
    error(['Could not find data file "training_history.csv".\n' ...
           'Please ensure training_history.csv is in the script folder or "results" subfolder.']);
end

outputFigPath    = fullfile(scriptDir, 'matlab_training_overview.png');
outputFigPathFig = fullfile(scriptDir, 'matlab_training_overview.fig');

% --- Figure Window Properties ---
figWidth  = 1100;    % Width in pixels
figHeight = 750;     % Height in pixels
fontName  = 'Helvetica';
titleFontSize = 12;
labelFontSize = 11;
axisFontSize  = 10;
superTitleFontSize = 15;

% --- Subplot 1: Cloud QNN Loss (Top-Left) ---
sub1_Color     = [0.90, 0.20, 0.20];  % Red (RGB: 0 to 1)
sub1_LineWidth = 2.0;
sub1_Title     = 'Cloud QNN Loss (\downarrow better)';
sub1_XLabel    = 'Epoch';
sub1_YLabel    = 'Cloud Loss (L_{assign})';
sub1_XLim      = [0, 100];            % Set [] for auto-scale, or e.g. [0, 100]
sub1_YLim      = [0.18, 0.30];        % Set [] for auto-scale, or e.g. [0.15, 0.32]

% --- Subplot 2: Edge QNN Loss (Top-Right) ---
sub2_Color     = [0.15, 0.70, 0.25];  % Green
sub2_LineWidth = 2.0;
sub2_Title     = 'Edge QNN Loss (\downarrow better)';
sub2_XLabel    = 'Epoch';
sub2_YLabel    = 'Edge Loss (L_{precode})';
sub2_XLim      = [0, 100];            % Set [] for auto-scale
sub2_YLim      = [0.65, 1.25];        % Set [] for auto-scale

% --- Subplot 3: Minimum User Rate (Bottom-Left) ---
sub3_Color     = [0.15, 0.40, 0.90];  % Blue
sub3_LineWidth = 2.0;
sub3_Title     = 'Minimum User Rate (\uparrow better)';
sub3_XLabel    = 'Epoch';
sub3_YLabel    = 'Min Rate [bits/s/Hz]';
sub3_XLim      = [0, 100];            % Set [] for auto-scale
sub3_YLim      = [0.90, 1.35];        % Set [] for auto-scale

% --- Subplot 4: Sum Rate (Bottom-Right) ---
sub4_Color     = [0.75, 0.15, 0.85];  % Magenta / Purple
sub4_LineWidth = 2.0;
sub4_Title     = 'Sum Rate (\uparrow better)';
sub4_XLabel    = 'Epoch';
sub4_YLabel    = 'Sum Rate [bits/s/Hz]';
sub4_XLim      = [0, 100];            % Set [] for auto-scale
sub4_YLim      = [8.50, 10.20];       % Set [] for auto-scale

% --- Grid Properties ---
enableGrid     = true;
gridLineStyle  = ':';                 % ':', '--', '-'
gridAlpha      = 0.6;                 % Transparency: 0 (invisible) to 1 (solid)

%% =========================================================================
%% 2. DATA IMPORT (ROBUST ACROSS ALL MATLAB VERSIONS)
%% =========================================================================

% Read CSV into table
try
    dataTbl = readtable(csvFilePath, 'VariableNamingRule', 'preserve');
catch
    dataTbl = readtable(csvFilePath);
end

% Extract columns using numeric indices (guarantees compatibility regardless of headers)
epochs    = dataTbl{:, 1};
cloudLoss = dataTbl{:, 2};
edgeLoss  = dataTbl{:, 3};
minRate   = dataTbl{:, 4};
sumRate   = dataTbl{:, 5};

%% =========================================================================
%% 3. PLOTTING (2x2 GRID)
%% =========================================================================

fig = figure('Color', 'w', 'Position', [100, 100, figWidth, figHeight]);

% --- (1) Cloud Loss ---
subplot(2, 2, 1);
plot(epochs, cloudLoss, 'Color', sub1_Color, 'LineWidth', sub1_LineWidth);
title(sub1_Title, 'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel(sub1_XLabel, 'FontSize', labelFontSize, 'FontName', fontName);
ylabel(sub1_YLabel, 'FontSize', labelFontSize, 'FontName', fontName);
set(gca, 'FontName', fontName, 'FontSize', axisFontSize);
if ~isempty(sub1_XLim), xlim(sub1_XLim); end
if ~isempty(sub1_YLim), ylim(sub1_YLim); end
if enableGrid
    grid on; ax = gca; ax.GridLineStyle = gridLineStyle; ax.GridAlpha = gridAlpha;
end

% --- (2) Edge Loss ---
subplot(2, 2, 2);
plot(epochs, edgeLoss, 'Color', sub2_Color, 'LineWidth', sub2_LineWidth);
title(sub2_Title, 'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel(sub2_XLabel, 'FontSize', labelFontSize, 'FontName', fontName);
ylabel(sub2_YLabel, 'FontSize', labelFontSize, 'FontName', fontName);
set(gca, 'FontName', fontName, 'FontSize', axisFontSize);
if ~isempty(sub2_XLim), xlim(sub2_XLim); end
if ~isempty(sub2_YLim), ylim(sub2_YLim); end
if enableGrid
    grid on; ax = gca; ax.GridLineStyle = gridLineStyle; ax.GridAlpha = gridAlpha;
end

% --- (3) Minimum User Rate ---
subplot(2, 2, 3);
plot(epochs, minRate, 'Color', sub3_Color, 'LineWidth', sub3_LineWidth);
title(sub3_Title, 'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel(sub3_XLabel, 'FontSize', labelFontSize, 'FontName', fontName);
ylabel(sub3_YLabel, 'FontSize', labelFontSize, 'FontName', fontName);
set(gca, 'FontName', fontName, 'FontSize', axisFontSize);
if ~isempty(sub3_XLim), xlim(sub3_XLim); end
if ~isempty(sub3_YLim), ylim(sub3_YLim); end
if enableGrid
    grid on; ax = gca; ax.GridLineStyle = gridLineStyle; ax.GridAlpha = gridAlpha;
end

% --- (4) Sum Rate ---
subplot(2, 2, 4);
plot(epochs, sumRate, 'Color', sub4_Color, 'LineWidth', sub4_LineWidth);
title(sub4_Title, 'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel(sub4_XLabel, 'FontSize', labelFontSize, 'FontName', fontName);
ylabel(sub4_YLabel, 'FontSize', labelFontSize, 'FontName', fontName);
set(gca, 'FontName', fontName, 'FontSize', axisFontSize);
if ~isempty(sub4_XLim), xlim(sub4_XLim); end
if ~isempty(sub4_YLim), ylim(sub4_YLim); end
if enableGrid
    grid on; ax = gca; ax.GridLineStyle = gridLineStyle; ax.GridAlpha = gridAlpha;
end

% Global Super-Title
if exist('sgtitle', 'file') || exist('sgtitle', 'builtin')
    sgtitle('Training Overview', 'FontSize', superTitleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
else
    annotation('textbox', [0 0.9 1 0.1], 'String', 'Training Overview', ...
        'EdgeColor', 'none', 'HorizontalAlignment', 'center', ...
        'FontSize', superTitleFontSize, 'FontWeight', 'bold');
end

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
        if savedFig, copyfile(outputFigPathFig, fullfile(pwd, 'matlab_training_overview.fig')); end
        if savedPng, copyfile(outputFigPath, fullfile(pwd, 'matlab_training_overview.png')); end
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
fprintf('  Training Overview plot completed successfully!\n');
fprintf('-------------------------------------------------------------\n\n');

