package org.example.nespresso.controller;

import org.example.nespresso.CoffeeObjectInputStream;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

import java.io.ByteArrayInputStream;
import java.util.Base64;

@Controller
public class CoffeeController {

    @ResponseBody
    @RequestMapping("/")
    public String index(){
        return "hello";
    }

    @ResponseBody
    @RequestMapping("/serve")
    public String coffee(String payload) {
        byte[] decode = Base64.getDecoder().decode(payload);
        try{
            new CoffeeObjectInputStream(new ByteArrayInputStream(decode)).readObject();
        } catch (Exception e) {
            return e.getMessage();
        }
        return "done!";
    }
}
