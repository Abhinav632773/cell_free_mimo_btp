%% =========================================================================
% run_all_plots.m
% 
% Master runner script for all Cell-Free MIMO / ISAC MATLAB plots:
%   1. plot_isac_pareto.m       -> ISAC Pareto Trade-off Front
%   2. plot_training_overview.m  -> 2x2 Training Loss & Rates Overview
%   3. plot_v2x_acceleration.m  -> Non-WSSUS V2X Dynamics & Acceleration Effects
%   4. plot_bench_channels.m    -> Benchmark E1 Channel Comparison (i.i.d. vs V2X)
%   5. plot_bench_ageing.m      -> Benchmark E2 CSI Ageing vs. Speed & Delay
%   6. plot_isac_topology.m     -> Cell-Free ISAC Network Topology & Beams
%
% Generates both native MATLAB .fig and high-res .png formats for EVERY plot.
% =========================================================================

close all;

scriptDir = fileparts(mfilename('fullpath'));
if isempty(scriptDir)
    scriptDir = pwd;
end

fprintf('\n=================================================================\n');
fprintf('  RUNNING ALL MATLAB PLOTS IN STANDALONE SUITE\n');
fprintf('  Target Directory: %s\n', scriptDir);
fprintf('=================================================================\n\n');

plotScripts = {
    'plot_isac_pareto.m', ...
    'plot_training_overview.m', ...
    'plot_v2x_acceleration.m', ...
    'plot_bench_channels.m', ...
    'plot_bench_ageing.m', ...
    'plot_isac_topology.m'
};

expectedFigFiles = {
    'matlab_isac_pareto.fig', ...
    'matlab_training_overview.fig', ...
    'matlab_v2x_acceleration.fig', ...
    'matlab_bench_E1_channels.fig', ...
    'matlab_bench_E2_ageing.fig', ...
    'matlab_isac_topology.fig'
};

expectedPngFiles = {
    'matlab_isac_pareto.png', ...
    'matlab_training_overview.png', ...
    'matlab_v2x_acceleration.png', ...
    'matlab_bench_E1_channels.png', ...
    'matlab_bench_E2_ageing.png', ...
    'matlab_isac_topology.png'
};

successCount = 0;

for idx = 1:numel(plotScripts)
    currentScript = plotScripts{idx};
    fullScriptPath = fullfile(scriptDir, currentScript);
    
    fprintf('-------------------------------------------------------------\n');
    fprintf('[%d/%d] Executing: %s ...\n', idx, numel(plotScripts), currentScript);
    fprintf('-------------------------------------------------------------\n');
    
    try
        run(fullScriptPath);
        successCount = successCount + 1;
        fprintf('  --> [%d/%d] Successfully finished %s!\n\n', idx, numel(plotScripts), currentScript);
    catch ME
        fprintf('  [ERROR] Running %s failed: %s\n\n', currentScript, ME.message);
    end
end

% Force MATLAB Current Folder view to refresh
try
    rehash;
catch
end

fprintf('\n=================================================================\n');
fprintf('  SUMMARY OF GENERATED PLOTS & OUTPUT FILES (%d/%d succeeded)\n', successCount, numel(plotScripts));
fprintf('=================================================================\n');

for k = 1:numel(expectedFigFiles)
    figPath = fullfile(scriptDir, expectedFigFiles{k});
    pngPath = fullfile(scriptDir, expectedPngFiles{k});
    
    figExists = exist(figPath, 'file') == 2;
    pngExists = exist(pngPath, 'file') == 2;
    
    if ~figExists
        figPath = fullfile(pwd, expectedFigFiles{k});
        figExists = exist(figPath, 'file') == 2;
    end
    if ~pngExists
        pngPath = fullfile(pwd, expectedPngFiles{k});
        pngExists = exist(pngPath, 'file') == 2;
    end
    
    fprintf('Plot %d: %-30s | .fig: %s | .png: %s\n', ...
        k, expectedPngFiles{k}, ...
        ternary(figExists, '[SAVED]', '[PENDING]'), ...
        ternary(pngExists, '[SAVED]', '[PENDING]'));
end

fprintf('=================================================================\n');
fprintf('  All outputs are saved in: %s\n', scriptDir);
fprintf('=================================================================\n\n');

function out = ternary(cond, valTrue, valFalse)
    if cond
        out = valTrue;
    else
        out = valFalse;
    end
end
