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
