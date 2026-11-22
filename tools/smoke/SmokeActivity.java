package org.g8rom.smoke;

import android.app.Activity;
import android.content.res.AssetFileDescriptor;
import android.content.res.Configuration;
import android.graphics.ImageFormat;
import android.graphics.Rect;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraMetadata;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.TotalCaptureResult;
import android.location.GnssStatus;
import android.location.LocationListener;
import android.location.LocationManager;
import android.hardware.camera2.CameraManager;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.ImageReader;
import android.media.MediaPlayer;
import android.media.MediaRecorder;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.TextView;

import java.util.List;

public final class SmokeActivity extends Activity {
    private static final String TAG = "G8RomSmoke";
    private final Handler main = new Handler(Looper.getMainLooper());
    private MediaPlayer player;

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        String test = getIntent().getStringExtra("test");
        Log.i(TAG, "start " + test);
        switch (test) {
            case "media" -> media(getIntent().getStringExtra("clip"));
            case "web" -> web();
            case "mic" -> new Thread(this::mic).start();
            case "torch" -> torch();
            case "gps" -> gps();
            case "camera" -> camera(getIntent().getStringExtra("lens"));
            case "pip" -> {
                TextView label = new TextView(this);
                label.setText("Picture-in-picture test");
                setContentView(label);
                main.postDelayed(() -> {
                    if (!enterPictureInPictureMode(new android.app.PictureInPictureParams.Builder()
                            .setSourceRectHint(new Rect(0, 0, label.getWidth(), label.getHeight()))
                            .build())) {
                        Log.e(TAG, "FAIL pip entry rejected");
                    }
                }, 1000);
            }
            default -> Log.e(TAG, "FAIL unknown test");
        }
    }

    private void media(String clip) {
        SurfaceView view = new SurfaceView(this);
        setContentView(view);
        view.getHolder().addCallback(new SurfaceHolder.Callback() {
            @Override
            public void surfaceCreated(SurfaceHolder surface) {
                try (AssetFileDescriptor asset = getAssets().openFd(clip + ".mp4")) {
                    player = new MediaPlayer();
                    player.setDataSource(asset.getFileDescriptor(), asset.getStartOffset(), asset.getLength());
                    player.setSurface(surface.getSurface());
                    player.setVolume(0.15f, 0.15f);
                    player.setOnPreparedListener(media -> {
                        Log.i(TAG, "media " + clip + " prepared " + media.getVideoWidth() + "x"
                                + media.getVideoHeight() + " tracks=" + media.getTrackInfo().length);
                        media.start();
                    });
                    player.setOnInfoListener((media, what, code) -> {
                        if (what == MediaPlayer.MEDIA_INFO_VIDEO_RENDERING_START) {
                            Log.i(TAG, "media " + clip + " rendered");
                        }
                        return false;
                    });
                    player.setOnCompletionListener(media -> Log.i(TAG, "PASS media " + clip
                            + " positionMs=" + media.getCurrentPosition() + " durationMs=" + media.getDuration()));
                    player.setOnErrorListener((media, what, code) -> {
                        Log.e(TAG, "FAIL media " + clip + " " + what + "/" + code);
                        return true;
                    });
                    player.prepareAsync();
                } catch (Exception e) {
                    Log.e(TAG, "FAIL media " + clip, e);
                }
            }

            @Override
            public void surfaceDestroyed(SurfaceHolder surface) {
                if (player != null) {
                    player.release();
                    player = null;
                }
            }

            @Override
            public void surfaceChanged(SurfaceHolder surface, int format, int width, int height) {}
        });
    }

    private void web() {
        WebView view = new WebView(this);
        view.getSettings().setJavaScriptEnabled(true);
        view.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView page, String url) {
                page.evaluateJavascript("""
                        (() => {
                          const canvas = document.querySelector('canvas');
                          const ctx = canvas.getContext('2d');
                          ctx.fillStyle = '#A02040';
                          ctx.fillRect(0, 0, 10, 10);
                          return Array.from(ctx.getImageData(1, 1, 1, 1).data).join(',');
                        })()
                        """, result -> {
                    if ("\"160,32,64,255\"".equals(result)) {
                        Log.i(TAG, "PASS web DOM JavaScript and canvas readback");
                    } else {
                        Log.e(TAG, "FAIL web canvas " + result);
                    }
                });
            }

            @Override
            public boolean onRenderProcessGone(WebView page, android.webkit.RenderProcessGoneDetail detail) {
                Log.e(TAG, "FAIL web render process gone");
                return true;
            }
        });
        setContentView(view);
        view.loadDataWithBaseURL(null, "<canvas width=64 height=64></canvas>", "text/html", "UTF-8", null);
    }

    private void mic() {
        int bytes = AudioRecord.getMinBufferSize(48000, AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT);
        if (bytes <= 0) {
            Log.e(TAG, "FAIL mic buffer size " + bytes);
            return;
        }
        try {
            AudioRecord record = new AudioRecord(MediaRecorder.AudioSource.MIC, 48000,
                    AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, bytes * 2);
            try {
                record.startRecording();
                short[] buffer = new short[2400];
                int total = 0;
                long samplesSquared = 0;
                while (total < 96000) {
                    int count = record.read(buffer, 0, buffer.length);
                    if (count <= 0) {
                        throw new IllegalStateException("AudioRecord read returned " + count);
                    }
                    for (int i = 0; i < count; i++) {
                        samplesSquared += (long) buffer[i] * buffer[i];
                    }
                    total += count;
                }
                double rms = Math.sqrt((double) samplesSquared / total);
                Log.i(TAG, (rms > 0 ? "PASS" : "FAIL") + " mic samples=" + total + " rms=" + rms);
            } finally {
                record.release();
            }
        } catch (Exception e) {
            Log.e(TAG, "FAIL mic", e);
        }
    }

    private void camera(String lens) {
        int facing = "front".equals(lens) ? CameraCharacteristics.LENS_FACING_FRONT
                : CameraCharacteristics.LENS_FACING_BACK;
        try {
            CameraManager manager = getSystemService(CameraManager.class);
            for (String id : manager.getCameraIdList()) {
                CameraCharacteristics characteristics = manager.getCameraCharacteristics(id);
                if (characteristics.get(CameraCharacteristics.LENS_FACING) == facing) {
                    if (!Integer.valueOf(CameraMetadata.INFO_DEVICE_TYPE_BUILT_IN)
                            .equals(characteristics.get(CameraCharacteristics.INFO_DEVICE_TYPE))) {
                        Log.e(TAG, "FAIL camera " + lens + " static built-in type");
                        return;
                    }
                    captureFrame(manager, id, lens);
                    return;
                }
            }
            Log.e(TAG, "FAIL camera " + lens + " missing");
        } catch (Exception e) {
            Log.e(TAG, "FAIL camera " + lens, e);
        }
    }

    private void captureFrame(CameraManager manager, String id, String lens) throws Exception {
        ImageReader reader = ImageReader.newInstance(640, 480, ImageFormat.YUV_420_888, 2);
        manager.openCamera(id, new CameraDevice.StateCallback() {
            @Override
            public void onOpened(CameraDevice camera) {
                boolean[] passed = new boolean[2];
                Runnable finish = () -> {
                    if (passed[0] && passed[1]) {
                        Log.i(TAG, "PASS camera " + lens + " YUV frame and BUILT_IN capture type");
                        camera.close();
                        reader.close();
                    }
                };
                reader.setOnImageAvailableListener(source -> {
                    try (var frame = source.acquireNextImage()) {
                        if (frame == null) {
                            return;
                        }
                        passed[0] = frame.getWidth() == 640 && frame.getHeight() == 480
                                && frame.getPlanes().length == 3;
                    }
                    finish.run();
                }, main);
                try {
                    camera.createCaptureSession(List.of(reader.getSurface()),
                            new CameraCaptureSession.StateCallback() {
                                @Override
                                public void onConfigured(CameraCaptureSession session) {
                                    try {
                                        var request = camera.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
                                        request.addTarget(reader.getSurface());
                                        session.capture(request.build(),
                                                new CameraCaptureSession.CaptureCallback() {
                                                    @Override
                                                    public void onCaptureCompleted(CameraCaptureSession active,
                                                            android.hardware.camera2.CaptureRequest request,
                                                            TotalCaptureResult result) {
                                                        passed[1] = Integer.valueOf(
                                                                CameraMetadata.INFO_DEVICE_TYPE_BUILT_IN)
                                                                .equals(result.get(CaptureResult.INFO_DEVICE_TYPE));
                                                        if (!passed[1]) {
                                                            Log.e(TAG, "FAIL camera " + lens
                                                                    + " frame lacks BUILT_IN type");
                                                            camera.close();
                                                            reader.close();
                                                        } else {
                                                            finish.run();
                                                        }
                                                    }
                                                }, main);
                                    } catch (Exception e) {
                                        Log.e(TAG, "FAIL camera request " + lens, e);
                                        camera.close();
                                        reader.close();
                                    }
                                }

                                @Override
                                public void onConfigureFailed(CameraCaptureSession session) {
                                    Log.e(TAG, "FAIL camera configuration " + lens);
                                    camera.close();
                                    reader.close();
                                }
                            }, main);
                } catch (Exception e) {
                    Log.e(TAG, "FAIL camera session " + lens, e);
                    camera.close();
                    reader.close();
                }
            }

            @Override
            public void onDisconnected(CameraDevice camera) {
                Log.e(TAG, "FAIL camera disconnected " + lens);
                camera.close();
                reader.close();
            }

            @Override
            public void onError(CameraDevice camera, int error) {
                Log.e(TAG, "FAIL camera " + lens + " error " + error);
                camera.close();
                reader.close();
            }
        }, main);
    }

    private void gps() {
        LocationManager location = getSystemService(LocationManager.class);
        if (!location.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
            Log.i(TAG, "SKIP gps provider disabled by user");
            return;
        }
        boolean[] status = new boolean[2];
        LocationListener listener = fix -> {
            status[1] = true;
            Log.i(TAG, "GPS actual fix received");
        };
        GnssStatus.Callback satellite = new GnssStatus.Callback() {
            @Override
            public void onStarted() {
                status[0] = true;
                Log.i(TAG, "GPS engine started");
            }

            @Override
            public void onSatelliteStatusChanged(GnssStatus data) {
                int used = 0;
                for (int i = 0; i < data.getSatelliteCount(); i++) {
                    if (data.usedInFix(i)) used++;
                }
                Log.i(TAG, "GPS satellites=" + data.getSatelliteCount() + " used=" + used);
            }
        };
        try {
            if (!location.registerGnssStatusCallback(getMainExecutor(), satellite)) {
                Log.e(TAG, "FAIL gps callback registration");
                return;
            }
            location.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000, 0,
                    getMainExecutor(), listener);
            main.postDelayed(() -> {
                location.removeUpdates(listener);
                location.unregisterGnssStatusCallback(satellite);
                Log.i(TAG, (status[0] ? "PASS" : "INCONCLUSIVE")
                        + " gps engine callback, fix=" + status[1]);
            }, 14_000);
        } catch (SecurityException | IllegalArgumentException e) {
            location.unregisterGnssStatusCallback(satellite);
            Log.e(TAG, "FAIL gps registration", e);
        }
    }

    private void torch() {
        try {
            CameraManager manager = getSystemService(CameraManager.class);
            for (String id : manager.getCameraIdList()) {
                CameraCharacteristics camera = manager.getCameraCharacteristics(id);
                if (camera.get(CameraCharacteristics.LENS_FACING) == CameraCharacteristics.LENS_FACING_BACK
                        && Boolean.TRUE.equals(camera.get(CameraCharacteristics.FLASH_INFO_AVAILABLE))) {
                    torch(manager, id);
                    return;
                }
            }
            Log.e(TAG, "FAIL torch rear camera flash missing");
        } catch (Exception e) {
            Log.e(TAG, "FAIL torch capability", e);
        }
    }

    private void torch(CameraManager manager, String id) throws Exception {
        CameraManager.TorchCallback listener = new CameraManager.TorchCallback() {
            private boolean seenOn;

            @Override
            public void onTorchModeChanged(String cameraId, boolean enabled) {
                if (!id.equals(cameraId)) {
                    return;
                }
                if (enabled) {
                    seenOn = true;
                } else if (seenOn) {
                    Log.i(TAG, "PASS torch off after on");
                    manager.unregisterTorchCallback(this);
                }
            }
        };
        manager.registerTorchCallback(listener, main);
        manager.setTorchMode(id, true);
        main.postDelayed(() -> {
            try {
                manager.setTorchMode(id, false);
            } catch (Exception e) {
                Log.e(TAG, "FAIL torch off", e);
            }
        }, 500);
    }

    @Override
    public void onPictureInPictureModeChanged(boolean inPip, Configuration config) {
        super.onPictureInPictureModeChanged(inPip, config);
        Log.i(TAG, inPip ? "PASS pip entered" : "pip exited");
    }
}
