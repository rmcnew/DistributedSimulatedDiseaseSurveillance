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

package com.liquidfortress.simulated_disease_survellience.messages;

import com.liquidfortress.simulated_disease_survellience.disease.Disease;
import com.liquidfortress.simulated_disease_survellience.main.Main;
import com.liquidfortress.simulated_disease_survellience.util.VectorTimestamp;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

/**
 * DiseaseCountMessageTest
 * <p/>
 * Tests for DiseaseCountMessage
 */
public class DiseaseCountMessageTest {

    DiseaseCountMessage diseaseCountMessage;

    @Before
    public void setup() {
        diseaseCountMessage = new DiseaseCountMessage(new VectorTimestamp(), 1, Disease.CHICKEN_POX, 2);
    }

    @Test
    public void serializeTest() {
        String serialized = Main.jsonb.toJson(diseaseCountMessage);
        System.out.println("DiseaseCountMessage serialized: " + serialized);
        Assert.assertNotNull(serialized);
    }
}
