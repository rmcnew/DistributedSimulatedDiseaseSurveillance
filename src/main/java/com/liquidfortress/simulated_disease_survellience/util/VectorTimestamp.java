/*
 * This file is part of Liquid Fortress Simulated Disease Survellience.
 * Copyright (c) 2018.  Richard Scott McNew.  All rights reserved.
 *
 * Developed by:  Richard Scott McNew
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this
 * software and associated documentation files (the "Software"), to deal with the
 * Software without restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
 * to permit persons to whom the Software is furnished to do so, subject to the
 * following conditions:
 *
 * Redistributions of source code must retain the above copyright notice, this list of
 * conditions and the following disclaimers.
 *
 * Redistributions in binary form must reproduce the above copyright notice, this list of
 * conditions and the following disclaimers in the documentation and/or other materials
 * provided with the distribution.
 *
 * Neither the names of Richard Scott McNew, Liquid Fortress, nor the names of its
 * contributors may be used to endorse or promote products derived from this Software
 * without specific prior written permission.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 * THE CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
 * DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
 * OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
 * THE USE OR OTHER DEALINGS WITH THE SOFTWARE.
 */

package com.liquidfortress.simulated_disease_survellience.util;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

/**
 * VectorTimestamp
 * <p/>
 * Implements vector timestamp
 */
public class VectorTimestamp {

    private final HashMap<Integer, Long> vector = new HashMap<>();

    public VectorTimestamp() {
    } // treat empty vector as all fields being zero

    public void update(VectorTimestamp vectorTimestamp, Integer nodeIdToIncrement) {
        incrementSelf(nodeIdToIncrement);
        if (vectorTimestamp != null && !vectorTimestamp.isEmpty()) {
            for (Map.Entry<Integer, Long> entry : vectorTimestamp.entrySet()) {
                Integer key = entry.getKey();
                Long entryValue = entry.getValue();
                // vector does not have this key, so add it
                vector.merge(key, entryValue, (a, b) -> Long.max(b, a));
            }
        }
    }

    public void incrementSelf(Integer nodeIdToIncrement) {
        vector.merge(nodeIdToIncrement, 1L, (a, b) -> (a + b));
    }

    public Long get(Object o) {
        Long value = vector.get(o);
        return (value != null) ? value : 0L; // treat empty vector as all fields being zero
    }

    private boolean isEmpty() {
        return vector.isEmpty();
    }

    private Set<Map.Entry<Integer, Long>> entrySet() {
        return vector.entrySet();
    }

    @Override
    public String toString() {
        StringBuilder builder = new StringBuilder("VectorTimestamp{");
        for (Map.Entry<Integer, Long> entry : this.entrySet()) {
            builder.append(entry.getKey());
            builder.append(" => ");
            builder.append(entry.getValue());
            builder.append("\n");
        }
        builder.append('}');
        return builder.toString();
    }
}
