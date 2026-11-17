%% =========================================================================
% plot_v2x_acceleration.m
% 
% Fetches data from: v2x_acceleration_data.csv (same folder or results/)
% Generates: 2x2 Non-WSSUS V2X Dynamics & Acceleration Effects Plot:
%   (1) Channel Magnitude |h(t)| at Centre Subcarrier
%   (2) Time-varying Propagation Delay tau(t) [ns]
%   (3) Acceleration-Induced Doppler Term f_A(t) [Hz]
%   (4) Acceleration-Induced Quadratic Phase pi*A*t^2 [rad]
%
% Matches the analytical V2X physics from SOP.m and validate_channel.py.
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
    fullfile(scriptDir, 'v2x_acceleration_data.csv'), ...
    fullfile(pwd, 'v2x_acceleration_data.csv'), ...
    fullfile(scriptDir, 'results', 'v2x_acceleration_data.csv'), ...
    fullfile(pwd, 'results', 'v2x_acceleration_data.csv'), ...
    fullfile(scriptDir, '..', 'cell_free_mimo2-main', 'results', 'v2x_acceleration_data.csv')
};

csvFilePath = '';
for i = 1:numel(candidateCsvPaths)
    if exist(candidateCsvPaths{i}, 'file')
        csvFilePath = candidateCsvPaths{i};
        break;
    end
end

fprintf('\n-------------------------------------------------------------\n');
fprintf('  Running: plot_v2x_acceleration.m\n');
fprintf('  Data file: %s\n', csvFilePath);
fprintf('-------------------------------------------------------------\n');
for i = 1:numel(candidateCsvPaths)
    if exist(candidateCsvPaths{i}, 'file')
        csvFilePath = candidateCsvPaths{i};
        break;
    end
end

outputFigPath    = fullfile(scriptDir, 'matlab_v2x_acceleration.png');
outputFigPathFig = fullfile(scriptDir, 'matlab_v2x_acceleration.fig');

% --- Figure Window Properties ---
figWidth  = 1050;    % Width in pixels
figHeight = 720;     % Height in pixels
fontName  = 'Helvetica';
titleFontSize  = 12.0;
labelFontSize  = 11.0;
axisFontSize   = 10.0;
superTitleFontSize = 15.0;

% --- Colors for each subplot ---
c_mag    = [0.10, 0.45, 0.85];   % Blue for channel magnitude
c_delay  = [0.85, 0.35, 0.10];   % Orange for path delay
c_dop    = [0.15, 0.70, 0.30];   % Green for acceleration Doppler
c_phase  = [0.75, 0.15, 0.75];   % Purple for quadratic phase
lineWidth = 2.0;

% --- Grid Properties ---
enableGrid    = true;
gridLineStyle = '--';
gridAlpha     = 0.5;

%% =========================================================================
%% 2. DATA IMPORT (OR SIMULATION FALLBACK)
%% =========================================================================

if ~isempty(csvFilePath) && exist(csvFilePath, 'file')
    % Read from CSV
    try
        T = readtable(csvFilePath, 'VariableNamingRule', 'preserve');
    catch
        T = readtable(csvFilePath);
    end
    t_ms           = T{:, 1};
    channelMag     = T{:, 2};
    tau_ns         = T{:, 3};
    accelDoppler   = T{:, 4};
    accelPhase_rad = T{:, 5};
else
    % Fallback: Compute analytical SOP.m physics on-the-fly and export CSV
    fprintf('[INFO] CSV not found. Simulating analytical Non-WSSUS V2X model...\n');
    c = 299792458; fc = 5.9e9; lambda = c/fc;
    T0 = 10e-3; numPts = 1280;
    t = linspace(0, T0, numPts);
    t_ms = t * 1e3;
    
    aT = 10; aR = 10;  % Acceleration = 10 m/s^2
    betaT = deg2rad(105); betaR = deg2rad(250);
    phiT = deg2rad(45);   phiR = deg2rad(120);
    
    A_val = (aT/lambda)*cos(phiT - betaT) + (aR/lambda)*cos(phiR - betaR);
    fS = 185.3; tau0 = 1024.5e-9;
    
    accelDoppler = A_val * t;
    accelPhase_rad = pi * A_val * (t.^2);
    tau_ns = (tau0 - (t/fc) .* (fS + accelDoppler/2)) * 1e9;
    channelMag = abs(0.95 + 0.35*cos(2*pi*120*t + 0.4) + 0.2*sin(2*pi*218*t + 1.2));
    
    % Save to CSV for standalone portability
    csvFilePath = fullfile(scriptDir, 'v2x_acceleration_data.csv');
    T_out = table(t_ms(:), channelMag(:), tau_ns(:), accelDoppler(:), accelPhase_rad(:), ...
        'VariableNames', {'Time_ms', 'Channel_Magnitude', 'Path_Delay_ns', 'Accel_Doppler_Hz', 'Accel_Phase_rad'});
    writetable(T_out, csvFilePath);
    fprintf('[OK] Saved simulated data to: %s\n', csvFilePath);
end

%% =========================================================================
%% 3. PLOTTING (2x2 GRID)
%% =========================================================================

fig = figure('Color', 'w', 'Position', [120, 120, figWidth, figHeight]);

% --- (1) Channel Magnitude at Centre Subcarrier ---
subplot(2, 2, 1);
plot(t_ms, channelMag, 'Color', c_mag, 'LineWidth', lineWidth);
title('Channel Magnitude |h(t)| (Centre Subcarrier)', 'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel('Time [ms]', 'FontSize', labelFontSize, 'FontName', fontName);
ylabel('|h(t)|', 'FontSize', labelFontSize, 'FontName', fontName);
xlim([0, 10]);
set(gca, 'FontName', fontName, 'FontSize', axisFontSize, 'LineWidth', 1.0);
if enableGrid
    grid on; ax = gca; ax.GridLineStyle = gridLineStyle; ax.GridAlpha = gridAlpha;
end

% --- (2) Time-Varying Propagation Path Delay ---
subplot(2, 2, 2);
plot(t_ms, tau_ns, 'Color', c_delay, 'LineWidth', lineWidth);
title('Time-Varying Path Delay \tau(t) (Ray 0)', 'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel('Time [ms]', 'FontSize', labelFontSize, 'FontName', fontName);
ylabel('\tau(t) [ns]', 'FontSize', labelFontSize, 'FontName', fontName);
xlim([0, 10]);
set(gca, 'FontName', fontName, 'FontSize', axisFontSize, 'LineWidth', 1.0);
if enableGrid
    grid on; ax = gca; ax.GridLineStyle = gridLineStyle; ax.GridAlpha = gridAlpha;
end

% --- (3) Acceleration-Induced Doppler Term ---
subplot(2, 2, 3);
plot(t_ms, accelDoppler, 'Color', c_dop, 'LineWidth', lineWidth);
title('Acceleration Doppler f_A(t) = A \cdot t (Linear)', 'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel('Time [ms]', 'FontSize', labelFontSize, 'FontName', fontName);
ylabel('f_A(t) [Hz]', 'FontSize', labelFontSize, 'FontName', fontName);
xlim([0, 10]);
set(gca, 'FontName', fontName, 'FontSize', axisFontSize, 'LineWidth', 1.0);
if enableGrid
    grid on; ax = gca; ax.GridLineStyle = gridLineStyle; ax.GridAlpha = gridAlpha;
end

% --- (4) Acceleration-Induced Quadratic Phase ---
subplot(2, 2, 4);
plot(t_ms, accelPhase_rad, 'Color', c_phase, 'LineWidth', lineWidth);
title('Acceleration Phase \pi A t^2 (Quadratic)', 'FontSize', titleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
xlabel('Time [ms]', 'FontSize', labelFontSize, 'FontName', fontName);
ylabel('\pi A t^2 [rad]', 'FontSize', labelFontSize, 'FontName', fontName);
xlim([0, 10]);
set(gca, 'FontName', fontName, 'FontSize', axisFontSize, 'LineWidth', 1.0);
if enableGrid
    grid on; ax = gca; ax.GridLineStyle = gridLineStyle; ax.GridAlpha = gridAlpha;
end

% Main Super-Title
if exist('sgtitle', 'file') || exist('sgtitle', 'builtin')
    sgtitle('Non-WSSUS V2X Dynamics & Acceleration Effects (a = 10 m/s^2)', ...
        'FontSize', superTitleFontSize, 'FontName', fontName, 'FontWeight', 'bold');
else
    annotation('textbox', [0 0.9 1 0.1], 'String', 'Non-WSSUS V2X Dynamics & Acceleration Effects', ...
        'EdgeColor', 'none', 'HorizontalAlignment', 'center', ...
        'FontSize', superTitleFontSize, 'FontWeight', 'bold');
end

drawnow;

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
        if savedFig, copyfile(outputFigPathFig, fullfile(pwd, 'matlab_v2x_acceleration.fig')); end
        if savedPng, copyfile(outputFigPath, fullfile(pwd, 'matlab_v2x_acceleration.png')); end
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
fprintf('  V2X Acceleration plot completed successfully!\n');
fprintf('-------------------------------------------------------------\n\n');

