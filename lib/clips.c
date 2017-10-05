/*
  Copyright (c) 2016-2017, Matteo Cafasso
  All rights reserved.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are met:

  1. Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.

  2. Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

  3. Neither the name of the copyright holder nor the names of its contributors
  may be used to endorse or promote products derived from this software without
  specific prior written permission.

  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
  OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
  OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
  WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
  OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#include <clips.h>

/* Python functions */
static void python_function(void *, DATA_OBJECT *);

int define_function(void *environment)
{
    return EnvDefineFunction(
        environment, "python-function", 'u',
        PTIEF python_function, "python-function");
}

/* Data Object */
short get_data_type(DATA_OBJECT *data)
{
  return GetpType(data);
}

short set_data_type(DATA_OBJECT *data, short type)
{
  return SetpType(data, type);
}

void *get_data_value(DATA_OBJECT *data)
{
  return GetpValue(data);
}

void *set_data_value(DATA_OBJECT *data, void *value)
{
  return SetpValue(data, value);
}

long get_data_begin(DATA_OBJECT *data)
{
  return GetpDOBegin(data);
}

long set_data_begin(DATA_OBJECT *data, long begin)
{
  return SetpDOBegin(data, begin);
}

long get_data_end(DATA_OBJECT *data)
{
  return GetpDOEnd(data);
}

long set_data_end(DATA_OBJECT *data, long end)
{
  return SetpDOEnd(data, end);
}

long get_data_length(DATA_OBJECT *data)
{
  return GetpDOLength(data);
}

/* Multifield */
short get_multifield_type(struct multifield *mf, long index)
{
  return GetMFType(mf, index);
}

short set_multifield_type(struct multifield *mf, long index, short type)
{
  return SetMFType(mf, index, type);
}

void *get_multifield_value(struct multifield *mf, long index)
{
  return GetMFValue(mf, index);
}

void *set_multifield_value(struct multifield *mf, long index, void *value)
{
  return SetMFValue(mf, index, value);
}

long get_multifield_length(struct multifield *mf)
{
  return GetMFLength(mf);
}

/* Hash Node */
char *to_string(struct symbolHashNode *data)
{
  return (char *) ValueToString(data);
}

long long to_integer(struct integerHashNode *data)
{
  return ValueToLong(data);
}

double to_double(struct floatHashNode *data)
{
  return ValueToDouble(data);
}

void *to_pointer(void *data)
{
  return ValueToPointer(data);
}

void *to_external_address(struct externalAddressHashNode *data)
{
  return ValueToExternalAddress(data);
}

/* Extra */
int implied_deftemplate(struct deftemplate *template)
{
    return template->implied;
}
