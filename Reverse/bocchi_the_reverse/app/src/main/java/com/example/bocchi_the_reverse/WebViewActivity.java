package com.example.bocchi_the_reverse;

import android.annotation.SuppressLint;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

public class WebViewActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_webview);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.webview_root), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        WebView webView = findViewById(R.id.webView);
        setupWebView(webView);
        //打印url参数
        Log.d("WebViewActivity", "Intent URL: " + getIntent().getStringExtra("url"));
        webView.loadUrl(resolveUrl(getIntent()));
    }

    @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
    private void setupWebView(WebView webView) {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(true);

        webView.addJavascriptInterface(new NativeVmBridge(), "bridge1");
        webView.addJavascriptInterface(new Bridge(this), "bridge2");
        webView.setWebViewClient(new InterceptingWebViewClient());
    }

    private String resolveUrl(Intent intent) {

        String extraUrl = intent.getStringExtra("url");
        if (extraUrl != null && !extraUrl.isEmpty()) {
            return extraUrl;
        }

        return "file:///android_asset/homepage.html";
    }

    private boolean handleUri(Uri uri) {
        String scheme = uri.getScheme();
        if (!"http".equalsIgnoreCase(scheme) && !"https".equalsIgnoreCase(scheme)) {
            return false;
        }

        Intent intent = new Intent(this, CheckFlagActivity.class);
        intent.putExtra("data", uri.getQueryParameter("data"));
        startActivity(intent);
        return true;
    }

    private class InterceptingWebViewClient extends WebViewClient {

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            return handleUri(request.getUrl());
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, String url) {
            return handleUri(Uri.parse(url));
        }
    }
}
