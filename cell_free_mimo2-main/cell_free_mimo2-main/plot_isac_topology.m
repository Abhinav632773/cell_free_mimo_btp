%% =========================================================================
% plot_isac_topology.m
% 
% Fetches data from: isac_topology.csv
% Generates: Cell-Free ISAC Network Topology (Communication + Radar Sensing)
%   - ISAC Access Points (DFRC Nodes)
%   - Communication Terminals (Users)
%   - Radar Sensing Target(s)
%   - Communication Links & Radar Probing Beams
%
% Matches the topology visualization in "isac_network.png".
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
    fullfile(scriptDir, 'isac_topology.csv'), ...
    fullfile(scriptDir, 'results', 'isac_topology.csv'), ...
    fullfile(pwd, 'isac_topology.csv'), ...
    fullfile(pwd, 'results', 'isac_topology.csv')
};

csvFilePath = '';
for i = 1:numel(candidateCsvPaths)
    if exist(candidateCsvPaths{i}, 'file')
        csvFilePath = candidateCsvPaths{i};
        break;
    end
end

if isempty(csvFilePath)
    error(['Could not find data file "isac_topology.csv".\n' ...
           'Please ensure isac_topology.csv is in the script folder.']);
end

outputFigPath    = fullfile(scriptDir, 'matlab_isac_topology.png');
outputFigPathFig = fullfile(scriptDir, 'matlab_isac_topology.fig');

% --- Figure Window Properties ---
figWidth  = 780;     % Width in pixels
figHeight = 680;     % Height in pixels
fontName  = 'Helvetica';
titleFontSize  = 13.0;
labelFontSize  = 11.5;
axisFontSize   = 10.0;
legendFontSize = 10.5;

% --- Colors and Markers ---
c_ap     = [0.00, 0.30, 0.90];   % Blue for ISAC Nodes
c_user   = [0.10, 0.65, 0.20];   % Green for Comm Users
c_target = [0.85, 0.10, 0.20];   % Crimson for Radar Target
c_beam   = [0.85, 0.20, 0.20];   % Dotted red for radar beams
c_link   = [0.20, 0.70, 0.20];   % Dashed green for comm links

% --- Grid Properties ---
enableGrid    = true;
gridLineStyle = ':';
gridAlpha     = 0.6;

%% =========================================================================
%% 2. DATA IMPORT
%% =========================================================================

try
    T = readtable(csvFilePath, 'VariableNamingRule', 'preserve');
catch
    T = readtable(csvFilePath);
end

nodeTypes = string(T{:, 1});
nodeIDs   = string(T{:, 2});
posX      = T{:, 3};
posY      = T{:, 4};

idxAP     = contains(nodeTypes, 'ISAC', 'IgnoreCase', true);
idxUser   = contains(nodeTypes, 'User', 'IgnoreCase', true);
idxTarget = contains(nodeTypes, 'Target', 'IgnoreCase', true);

apX = posX(idxAP);     apY = posY(idxAP);     apIDs = nodeIDs(idxAP);
userX = posX(idxUser); userY = posY(idxUser); userIDs = nodeIDs(idxUser);
tgtX = posX(idxTarget); tgtY = posY(idxTarget); tgtIDs = nodeIDs(idxTarget);

%% =========================================================================
%% 3. PLOTTING
%% =========================================================================

fig = figure('Color', 'w', 'Position', [150, 100, figWidth, figHeight]);
hold on; box on;

% 1. Draw Radar Probing Beams (all APs pointing to target 1)
for m = 1:length(apX)
    hBeam = plot([apX(m), tgtX(1)], [apY(m), tgtY(1)], ':', 'Color', c_beam, ...
        'LineWidth', 1.3, 'DisplayName', 'Radar Probing Beam');
end

% 2. Draw Sample Communication Links (each AP serving nearest user)
for m = 1:length(apX)
    dists = sqrt((userX - apX(m)).^2 + (userY - apY(m)).^2);
    [~, bestU] = min(dists);
    hLink = plot([apX(m), userX(bestU)], [apY(m), userY(bestU)], '--', 'Color', c_link, ...
        'LineWidth', 1.5, 'DisplayName', 'Comm Association Link');
end

% 3. Plot ISAC Nodes
hAP = scatter(apX, apY, 140, 's', 'MarkerEdgeColor', c_ap, 'MarkerFaceColor', c_ap, ...
    'DisplayName', 'ISAC Nodes (DFRC)');
for m = 1:length(apX)
    text(apX(m), apY(m) + 16, apIDs(m), 'Color', c_ap, 'FontSize', 9.5, ...
        'FontName', fontName, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
end

% 4. Plot Comm Users
hUser = scatter(userX, userY, 110, 'o', 'MarkerEdgeColor', c_user, 'MarkerFaceColor', c_user, ...
    'DisplayName', 'Comm Users');
for k = 1:length(userX)
    text(userX(k), userY(k) - 18, userIDs(k), 'Color', c_user, 'FontSize', 9.5, ...
        'FontName', fontName, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
end

% 5. Plot Radar Sensing Target(s)
hTarget = scatter(tgtX, tgtY, 260, 'p', 'MarkerEdgeColor', c_target, 'MarkerFaceColor', c_target, ...
    'DisplayName', 'Radar Sensing Target');
for t = 1:length(tgtX)
    text(tgtX(t), tgtY(t) + 18, tgtIDs(t), 'Color', c_target, 'FontSize', 10.5, ...
        'FontName', fontName, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
end

% Title & Axis Labels
title('Cell-Free ISAC Network Topology (Communication + Radar Sensing)', ...
    'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel('X Coordinate [m]', 'FontSize', labelFontSize, 'FontName', fontName);
ylabel('Y Coordinate [m]', 'FontSize', labelFontSize, 'FontName', fontName);
set(gca, 'FontName', fontName, 'FontSize', axisFontSize, 'LineWidth', 1.0);
xlim([0, 500]);
ylim([0, 500]);

if enableGrid
    grid on; ax = gca; ax.GridLineStyle = gridLineStyle; ax.GridAlpha = gridAlpha;
end

legend([hAP, hUser, hTarget, hBeam, hLink], 'Location', 'northeast', 'FontSize', legendFontSize);

hold off;

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
    fprintf('[OK] ISAC Topology plot (.fig format) saved to: %s\n', outputFigPathFig);
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
    fprintf('[OK] ISAC Topology plot (.png format) saved to: %s\n', outputFigPath);
end

% Also mirror to Current Working Directory if different
if ~strcmp(pwd, scriptDir)
    try
        if savedFig, copyfile(outputFigPathFig, fullfile(pwd, 'matlab_isac_topology.fig')); end
        if savedPng, copyfile(outputFigPath, fullfile(pwd, 'matlab_isac_topology.png')); end
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
fprintf('  ISAC Topology plot completed successfully!\n');
fprintf('-------------------------------------------------------------\n\n');

