package org.example.nespresso;

import java.io.*;
import java.util.*;

public class CoffeeObjectInputStream extends ObjectInputStream {
    private static ArrayList<String> BLACKLIST = new ArrayList<>();

    static {
        BLACKLIST.add("java.swing");
        BLACKLIST.add("java.security");
        BLACKLIST.add("org.spingframework.aop.target");
    }

    public CoffeeObjectInputStream(InputStream in) throws IOException {
        super(in);
    }

    @Override
    protected Class<?> resolveClass(ObjectStreamClass desc) throws IOException, ClassNotFoundException {
        Iterator<String> it = BLACKLIST.iterator();
        while (it.hasNext()) {
            String s = it.next();
            if (desc.getName().startsWith(s)) {
                throw new InvalidClassException("No no no: ", desc.getName());
            }
        }
        return super.resolveClass(desc);
    }
}
