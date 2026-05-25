package com.example.bocchi_the_reverse;

import android.graphics.BitmapFactory;
import android.os.Bundle;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import java.io.InputStream;

public class CheckFlagActivity extends AppCompatActivity {

    private static final String EXPECTED_CIPHER = "f69d999250efb20d8307c27c66e7ccc0314f5f4d3b250221b14f3de05123c610ccde7ce9ef5a23ab4ddbd7f150769ce72dc6eb1643edecd59b529e1a57101d03";
    private static final String EXPECTED_FLAG = "This app involves major national security issues. If you are reverse engineering it, please stop immediately.";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_check_flag);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.check_flag_root), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        ImageView resultImageView = findViewById(R.id.resultImageView);
        TextView resultTextView = findViewById(R.id.resultTextView);

        String data = getIntent().getStringExtra("data");
        boolean success;
        if (EXPECTED_FLAG.equalsIgnoreCase(data == null ? "" : data)) {
            success = false;
        }
        else {
            success = EXPECTED_CIPHER.equalsIgnoreCase(data == null ? "" : data);
        }


        if (success) {
            resultTextView.setText("flag对啦，我终于可以练吉他了！");
            loadAssetImage(resultImageView, "ccs/ccs/success.png");
        } else {
            resultTextView.setText("flag错了，我的作业写不完了😭");
            loadAssetImage(resultImageView, "ccs/ccs/failed.png");
        }
    }

    private void loadAssetImage(ImageView imageView, String assetPath) {
        try (InputStream inputStream = getAssets().open(assetPath)) {
            imageView.setImageBitmap(BitmapFactory.decodeStream(inputStream));
        } catch (Exception e) {
            throw new IllegalStateException("Failed to load asset image: " + assetPath, e);
        }
    }
}
