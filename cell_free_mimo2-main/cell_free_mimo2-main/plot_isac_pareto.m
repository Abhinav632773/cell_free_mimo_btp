%% =========================================================================
% plot_isac_pareto.m
% 
% Fetches data from: isac_pareto.csv (same folder or results/)
% Generates: ISAC Pareto Trade-off Front (Comm Min Rate vs. Radar Sensing SNR)
% Exactly matches the visual comparison in "cell_free_mimo2-mainimagr.jpeg"
%
% All styling parameters (axes limits, labels, colors, font sizes, markers,
% line widths, annotations) are placed in the EDITABLE PARAMETERS section below.
% =========================================================================

close all;

%% =========================================================================
%% 1. EDITABLE PARAMETERS (CUSTOMIZE AXES, LABELS, COLORS, ANNOTATIONS HERE)
%% =========================================================================

% --- File Paths (Auto-resolves relative to script directory) ---
scriptDir = fileparts(mfilename('fullpath'));
if isempty(scriptDir)
    scriptDir = pwd;
end

candidateCsvPaths = {
    fullfile(scriptDir, 'isac_pareto.csv'), ...
    fullfile(pwd, 'isac_pareto.csv'), ...
    fullfile(scriptDir, 'results', 'isac_pareto.csv'), ...
    fullfile(pwd, 'results', 'isac_pareto.csv'), ...
    fullfile(scriptDir, '..', 'cell_free_mimo2-main', 'results', 'isac_pareto.csv'), ...
    fullfile(scriptDir, '..', 'final_res', 'isac_pareto.csv')
};

csvFilePath = '';
for i = 1:numel(candidateCsvPaths)
    if exist(candidateCsvPaths{i}, 'file')
        csvFilePath = candidateCsvPaths{i};
        break;
    end
end

if isempty(csvFilePath)
    error('Could not find isac_pareto.csv in %s or %s', scriptDir, pwd);
end

fprintf('\n-------------------------------------------------------------\n');
fprintf('  Running: plot_isac_pareto.m\n');
fprintf('  Data file: %s\n', csvFilePath);
fprintf('-------------------------------------------------------------\n');

if isempty(csvFilePath)
    error(['Could not find data file "isac_pareto.csv".\n' ...
           'Please ensure isac_pareto.csv is in the script folder or "results" subfolder.']);
end

outputFigPath    = fullfile(scriptDir, 'matlab_isac_pareto.png');
outputFigPathFig = fullfile(scriptDir, 'matlab_isac_pareto.fig');

% --- Figure Window Properties ---
figWidth  = 950;     % Width in pixels
figHeight = 620;     % Height in pixels
fontName  = 'Helvetica';
titleFontSize  = 13;
labelFontSize  = 11.5;
axisFontSize   = 10.5;
legendFontSize = 11;
annotFontSize  = 9.5;

% --- Main Titles & Axis Labels ---
plotTitle = 'ISAC Pareto Trade-off Front: Comm Min Rate vs. Radar Sensing SNR';
xLabelStr = 'Target Radar Echo SNR [dB]';
yLabelStr = 'Min User Communication Rate [bits/s/Hz]';

% --- Axis Limits & Ticks (Set to [] for auto-scaling) ---
xLimits = [40.5, 44.6];               % X-axis range: [min, max]
yLimits = [0.4, 3.7];                 % Y-axis range: [min, max]
xTicks  = 40.5:0.5:44.5;              % Explicit X tick marks
yTicks  = 0.5:0.5:3.5;                % Explicit Y tick marks

% --- Curve 1: Search-based + DFRC ---
c1_Name       = 'Search-based + DFRC';
c1_Color      = [1.00, 0.50, 0.00];   % Vivid Orange
c1_Marker     = 's';                  % Square
c1_MarkerSize = 7;
c1_LineWidth  = 2.2;

% --- Curve 2: QNN + DFRC (Proposed) ---
c2_Name       = 'QNN + DFRC';
c2_Color      = [0.00, 0.10, 0.90];   % Vivid Blue
c2_Marker     = 'o';                  % Circle
c2_MarkerSize = 7;
c2_LineWidth  = 2.2;

% --- Curve 3: Random + DFRC ---
c3_Name       = 'Random + DFRC';
c3_Color      = [0.50, 0.50, 0.50];   % Grey
c3_Marker     = '^';                  % Triangle
c3_MarkerSize = 7;
c3_LineWidth  = 2.2;

% --- Annotations (eta = 0.0, 0.2, 0.5, 0.85) ---
showAnnotations = true;
annotEtas = [0.0, 0.2, 0.5, 0.85];   % Power ratios to annotate

% Offset (dx, dy) for annotation text placement to prevent overlapping
annotOffsets = containers.Map();
% Support both '0' and '0.0' key formats
annotOffsets('Search_0')    = [-0.08,  0.08];
annotOffsets('Search_0.0')  = [-0.08,  0.08];
annotOffsets('Search_0.2')  = [ 0.01,  0.08];
annotOffsets('Search_0.5')  = [ 0.01,  0.08];
annotOffsets('Search_0.85') = [ 0.01,  0.08];

annotOffsets('QNN_0')       = [-0.06,  0.08];
annotOffsets('QNN_0.0')     = [-0.06,  0.08];
annotOffsets('QNN_0.2')     = [ 0.01,  0.08];
annotOffsets('QNN_0.5')     = [ 0.02,  0.08];
annotOffsets('QNN_0.85')    = [ 0.01,  0.08];

annotOffsets('Random_0')    = [-0.10,  0.08];
annotOffsets('Random_0.0')  = [-0.10,  0.08];
annotOffsets('Random_0.2')  = [-0.10,  0.08];
annotOffsets('Random_0.5')  = [ 0.01,  0.08];
annotOffsets('Random_0.85') = [ 0.01,  0.08];

% --- Grid & Legend ---
enableGrid    = true;
gridLineStyle = '--';
gridAlpha     = 0.5;
legendLocation = 'northeast';

%% =========================================================================
%% 2. DATA IMPORT & EXTRACTION
%% =========================================================================

try
    T = readtable(csvFilePath, 'VariableNamingRule', 'preserve');
catch
    T = readtable(csvFilePath);
end

% Columns:
% 1: Radar Power Ratio (eta)
% 2: Method
% 3: Min Comm Rate [bits/s/Hz]
% 4: Radar Echo SNR [dB]
% 5: Sensing Rate [bits/s/Hz]

etaCol     = T{:, 1};
methodCol  = string(T{:, 2});
commRate   = T{:, 3};
radarSNR   = T{:, 4};

% Filter points per method
idxSearch = contains(methodCol, 'Search', 'IgnoreCase', true);
idxQNN    = contains(methodCol, 'QNN', 'IgnoreCase', true);
idxRandom = contains(methodCol, 'Random', 'IgnoreCase', true);

search_SNR  = radarSNR(idxSearch);
search_Rate = commRate(idxSearch);
search_eta  = etaCol(idxSearch);

qnn_SNR     = radarSNR(idxQNN);
qnn_Rate    = commRate(idxQNN);
qnn_eta     = etaCol(idxQNN);

rand_SNR    = radarSNR(idxRandom);
rand_Rate   = commRate(idxRandom);
rand_eta    = etaCol(idxRandom);

%% =========================================================================
%% 3. PLOTTING
%% =========================================================================

fig = figure('Color', 'w', 'Position', [150, 150, figWidth, figHeight]);
hold on; box on;

% Plot Curves
h1 = plot(search_SNR, search_Rate, '-', 'Color', c1_Color, ...
    'LineWidth', c1_LineWidth, 'Marker', c1_Marker, 'MarkerSize', c1_MarkerSize, ...
    'MarkerFaceColor', c1_Color, 'DisplayName', c1_Name);

h2 = plot(qnn_SNR, qnn_Rate, '-', 'Color', c2_Color, ...
    'LineWidth', c2_LineWidth, 'Marker', c2_Marker, 'MarkerSize', c2_MarkerSize, ...
    'MarkerFaceColor', c2_Color, 'DisplayName', c2_Name);

h3 = plot(rand_SNR, rand_Rate, '-', 'Color', c3_Color, ...
    'LineWidth', c3_LineWidth, 'Marker', c3_Marker, 'MarkerSize', c3_MarkerSize, ...
    'MarkerFaceColor', c3_Color, 'DisplayName', c3_Name);

% Add Annotations (\eta = ...)
if showAnnotations
    for i = 1:length(annotEtas)
        targetEta = annotEtas(i);
        etaStr = sprintf('%g', targetEta);
        
        % Search
        k = find(abs(search_eta - targetEta) < 1e-4, 1);
        if ~isempty(k)
            kName = ['Search_' etaStr];
            if isKey(annotOffsets, kName)
                off = annotOffsets(kName);
            elseif isKey(annotOffsets, sprintf('Search_%.1f', targetEta))
                off = annotOffsets(sprintf('Search_%.1f', targetEta));
            else
                off = [0.01, 0.08];
            end
            text(search_SNR(k) + off(1), search_Rate(k) + off(2), ...
                 sprintf('\\eta=%g', targetEta), ...
                 'Color', c1_Color, 'FontSize', annotFontSize, ...
                 'FontName', fontName, 'FontWeight', 'bold');
        end
        
        % QNN
        k = find(abs(qnn_eta - targetEta) < 1e-4, 1);
        if ~isempty(k)
            kName = ['QNN_' etaStr];
            if isKey(annotOffsets, kName)
                off = annotOffsets(kName);
            elseif isKey(annotOffsets, sprintf('QNN_%.1f', targetEta))
                off = annotOffsets(sprintf('QNN_%.1f', targetEta));
            else
                off = [0.01, 0.08];
            end
            text(qnn_SNR(k) + off(1), qnn_Rate(k) + off(2), ...
                 sprintf('\\eta=%g', targetEta), ...
                 'Color', c2_Color, 'FontSize', annotFontSize, ...
                 'FontName', fontName, 'FontWeight', 'bold');
        end
        
        % Random
        k = find(abs(rand_eta - targetEta) < 1e-4, 1);
        if ~isempty(k)
            kName = ['Random_' etaStr];
            if isKey(annotOffsets, kName)
                off = annotOffsets(kName);
            elseif isKey(annotOffsets, sprintf('Random_%.1f', targetEta))
                off = annotOffsets(sprintf('Random_%.1f', targetEta));
            else
                off = [0.01, 0.08];
            end
            text(rand_SNR(k) + off(1), rand_Rate(k) + off(2), ...
                 sprintf('\\eta=%g', targetEta), ...
                 'Color', c3_Color, 'FontSize', annotFontSize, ...
                 'FontName', fontName, 'FontWeight', 'bold');
        end
    end
end

% Axes Styling
title(plotTitle, 'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel(xLabelStr, 'FontSize', labelFontSize, 'FontName', fontName, 'FontWeight', 'normal');
ylabel(yLabelStr, 'FontSize', labelFontSize, 'FontName', fontName, 'FontWeight', 'normal');
set(gca, 'FontName', fontName, 'FontSize', axisFontSize, 'LineWidth', 1.0);

if ~isempty(xLimits), xlim(xLimits); end
if ~isempty(yLimits), ylim(yLimits); end
if ~isempty(xTicks),  xticks(xTicks); end
if ~isempty(yTicks),  yticks(yTicks); end

if enableGrid
    grid on;
    ax = gca;
    ax.GridLineStyle = gridLineStyle;
    ax.GridAlpha = gridAlpha;
end

% Legend
lgd = legend([h1, h2, h3], 'Location', legendLocation, 'FontSize', legendFontSize, 'FontName', fontName);
set(lgd, 'EdgeColor', [0.8, 0.8, 0.8]);

hold off;
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
        if savedFig, copyfile(outputFigPathFig, fullfile(pwd, 'matlab_isac_pareto.fig')); end
        if savedPng, copyfile(outputFigPath, fullfile(pwd, 'matlab_isac_pareto.png')); end
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
fprintf('  ISAC Pareto plot completed successfully!\n');
fprintf('-------------------------------------------------------------\n\n');

