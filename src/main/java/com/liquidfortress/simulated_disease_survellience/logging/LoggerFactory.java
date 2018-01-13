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

package com.liquidfortress.simulated_disease_survellience.logging;

import com.liquidfortress.simulated_disease_survellience.cli_args.ValidatedArgs;
import org.apache.logging.log4j.Level;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.core.Logger;
import org.apache.logging.log4j.core.LoggerContext;
import org.apache.logging.log4j.core.appender.ConsoleAppender;
import org.apache.logging.log4j.core.appender.FileAppender;
import org.apache.logging.log4j.core.config.AppenderRef;
import org.apache.logging.log4j.core.config.Configuration;
import org.apache.logging.log4j.core.config.LoggerConfig;
import org.apache.logging.log4j.core.layout.PatternLayout;


/**
 * LoggerFactory
 * <p/>
 * Get a logger for console and / or file output based on command line args
 */
public class LoggerFactory {

    private static final String CONSOLE_APPENDER = "CONSOLE_APPENDER";
    private static final String FILE_APPENDER = "FILE_APPENDER";
    private static final String LOGGER_NAME = "LFSDS_LOGGER";
    private static final Level DEFAULT_LEVEL = Level.INFO;
    private static final Level VERBOSE_LEVEL = Level.TRACE;

    /**
     * Get the logger used for output
     *
     * @param validatedArgs with output file, silent, and verbose options that
     *                      are used to configure the logger
     * @return Logger with dynamically-generated configuration
     */
    public static Logger getLogger(ValidatedArgs validatedArgs) {
        // This approach is ugly, but it circumvents the need for multiple log4j
        // configuration files and simplifies writing results to the console and the output file
        // Silence StatusLogger
        System.setProperty("org.apache.logging.log4j.simplelog.StatusLogger.level", "FATAL");
        // Setup context
        LoggerContext loggerContext = (LoggerContext) LogManager.getContext(false);
        Configuration configuration = loggerContext.getConfiguration();
        // Define layout
        PatternLayout patternLayout = PatternLayout.newBuilder()
                .withConfiguration(configuration)
                // uncomment this pattern for debugging
                .withPattern("%d{ISO8601} [%level] [%F:%L] %msg%n")
                .build();
        // Add appenders
        AppenderRef[] appenderRefs;
        //// Create console appender unless silent
        ConsoleAppender consoleAppender = null;
        AppenderRef consoleAppenderRef = null;
        if (!validatedArgs.silent) {
            consoleAppender = ConsoleAppender.newBuilder()
                    .setConfiguration(configuration)
                    .withLayout(patternLayout)
                    .withName(CONSOLE_APPENDER)
                    .build();
            consoleAppender.start();
            configuration.addAppender(consoleAppender);
            consoleAppenderRef = AppenderRef.createAppenderRef(CONSOLE_APPENDER, null, null);
        }
        //// Create file appender if output file specified
        FileAppender fileAppender = null;
        AppenderRef fileAppenderRef = null;
        if (validatedArgs.outputFile != null) {
            fileAppender = FileAppender.newBuilder()
                    .setConfiguration(configuration)
                    .withLayout(patternLayout)
                    .withName(FILE_APPENDER)
                    .withFileName(validatedArgs.outputFile.getAbsolutePath())
                    .build();
            fileAppender.start();
            configuration.addAppender(fileAppender);
            fileAppenderRef = AppenderRef.createAppenderRef(FILE_APPENDER, null, null);
        }
        if ((consoleAppenderRef != null) && (fileAppenderRef != null)) {
            appenderRefs = new AppenderRef[]{consoleAppenderRef, fileAppenderRef};
        } else if (consoleAppenderRef != null) {
            appenderRefs = new AppenderRef[]{consoleAppenderRef};
        } else if (fileAppenderRef != null) {
            appenderRefs = new AppenderRef[]{fileAppenderRef};
        } else {
            throw new IllegalStateException("At least one appender must be configured to provide output!");
        }
        // Build and update the LoggerConfig
        Level levelToUse = validatedArgs.verbose ? VERBOSE_LEVEL : DEFAULT_LEVEL;
        LoggerConfig loggerConfig = LoggerConfig.createLogger(false, levelToUse, LOGGER_NAME, "true", appenderRefs, null, configuration, null);
        if (consoleAppender != null) {
            loggerConfig.addAppender(consoleAppender, null, null);
        }
        if (fileAppender != null) {
            loggerConfig.addAppender(fileAppender, null, null);
        }
        configuration.addLogger(LOGGER_NAME, loggerConfig);
        loggerContext.updateLoggers();
        return (Logger) LogManager.getLogger(LOGGER_NAME);
    }

}
