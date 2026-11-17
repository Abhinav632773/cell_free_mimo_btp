%% ============================================================
% SOP.m - NON-WSSUS V2X CHANNEL RESPONSE WITH ACCELERATION
% ============================================================
% Reproduces the core V2X physical channel simulation from the paper.
% Generates Figures 1-4 and saves both .fig and .png files.

close all;
rng(10);

scriptDir = fileparts(mfilename('fullpath'));
if isempty(scriptDir)
    scriptDir = pwd;
end

c = 299792458;                  % Speed of light [m/s]
fc = 5.9e9;                     % Carrier frequency [Hz]
B = 10e6;                       % Bandwidth [Hz]
N = 64;                         % Number of subcarriers
d = 30;                         % Ring radius [m]
D = 300;                        % Initial Tx-Rx distance [m]
T0 = 10e-3;                     % 10 ms, OBSERVATION INTERVAL
numSymbols = 1280;
t = linspace(0, T0, numSymbols);

% Velocities [m/s]
vT = 40/3.6; vR = 40/3.6;

% Directions of motion [rad]
gammaT = deg2rad(105); gammaR = deg2rad(70);

% Directions of acceleration [rad]
betaT = deg2rad(105); betaR = deg2rad(250);

% Accelerations [m/s^2]
aT = 10; aR = 10;

% Derived parameters
lambda = c/fc;
deltaF = B/N;
fmaxT = vT/lambda; fmaxR = vR/lambda;
L = 100;
k = (-N/2:N/2-1).';
fSub = k*deltaF;

% Random path phases
theta = -pi + 2*pi*rand(L, 1);
g = sqrt(randn(L, 1).^2 + randn(L, 1).^2);
g = g/sqrt(sum(abs(g).^2));
phiR = -pi + 2*pi*rand(L, 1);

% One-ring geometry
xR = 0; yR = 0;
xT = D; yT = 0;
xS = d*cos(phiR); yS = d*sin(phiR);

dR = sqrt((xS-xR).^2 + (yS-yR).^2);
dT = sqrt((xS-xT).^2 + (yS-yT).^2);
phiRgeom = atan2(yS-yR, xS-xR);
phiT = atan2(yS-yT, xS-xT);

tau0 = (dT+dR)/c;
fS = fmaxT*cos(phiT-gammaT) + fmaxR*cos(phiRgeom-gammaR);
A = (aT/lambda)*cos(phiT-betaT) + (aR/lambda)*cos(phiRgeom-betaR);

H = zeros(N, numSymbols);
tauMatrix = zeros(L, numSymbols);
fAMatrix = zeros(L, numSymbols);

fprintf('Generating V2X channel time-evolution across %d symbols...\n', numSymbols);
for it = 1:numSymbols
    tt = t(it);
    fA = A*tt;
    fAMatrix(:, it) = fA;
    tau = tau0 - (tt/fc).*(fS + fA/2);
    tauMatrix(:, it) = tau;

    for ik = 1:N
        totalPhase = theta + 2*pi*tau.*(fc + fSub(ik));
        H(ik, it) = sum(g .* exp(-1j*totalPhase));
    end
end

[~, centerSC] = min(abs(fSub));
Hresponse = H(centerSC, :);
pathIndex = 1;

% Save data to CSV for standalone convenience
csvPath = fullfile(scriptDir, 'v2x_acceleration_data.csv');
phiAccelerationPDF = pi*A(pathIndex).*(t.^2);
T_data = table((t*1e3)', abs(Hresponse)', (tauMatrix(pathIndex,:)*1e9)', ...
    fAMatrix(pathIndex,:)', phiAccelerationPDF', ...
    'VariableNames', {'Time_ms', 'Channel_Magnitude', 'Path_Delay_ns', 'Accel_Doppler_Hz', 'Accel_Phase_rad'});
writetable(T_data, csvPath);
fprintf('[OK] V2X acceleration data exported to: %s\n', csvPath);

drawnow;
pause(0.2);

save_robust = @(h, baseName) save_pair(h, scriptDir, baseName);
save_robust(f1, 'matlab_sop_fig1');
save_robust(f2, 'matlab_sop_fig2');
save_robust(f3, 'matlab_sop_fig3');
save_robust(f4, 'matlab_sop_fig4');

try, rehash; catch, end

fprintf('\n[OK] All 4 SOP figures saved as both .fig and .png in: %s\n', scriptDir);

function save_pair(h, dirPath, name)
    drawnow;
    figPath = fullfile(dirPath, [name, '.fig']);
    pngPath = fullfile(dirPath, [name, '.png']);
    try
        savefig(h, figPath);
    catch
        try
            saveas(h, figPath);
        catch
            try, figure(h); savefig(figPath); catch, end
        end
    end
    try
        if exist('exportgraphics', 'file') || exist('exportgraphics', 'builtin')
            exportgraphics(h, pngPath, 'Resolution', 300);
        else
            print(h, pngPath, '-dpng', '-r300');
        end
    catch
        try, saveas(h, pngPath); catch, end
    end
    if ~strcmp(pwd, dirPath)
        try
            if exist(figPath, 'file'), copyfile(figPath, fullfile(pwd, [name, '.fig'])); end
            if exist(pngPath, 'file'), copyfile(pngPath, fullfile(pwd, [name, '.png'])); end
        catch
        end
    end
end

